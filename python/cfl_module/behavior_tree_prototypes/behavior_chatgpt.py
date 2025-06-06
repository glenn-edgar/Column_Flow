import psycopg2
import psycopg2.extras
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    Iterable,
    overload,
)
import math
import re

# ───────────────────────────────────────────────────────────────────────────
#  Type aliases
# ───────────────────────────────────────────────────────────────────────────
PathType = Union[str, List[str], Tuple[str, ...]]

# ───────────────────────────────────────────────────────────────────────────
#  LabelPattern: a single “atomic” pattern (e.g.  “foo*” or “bar@” or “baz”)
# ───────────────────────────────────────────────────────────────────────────
class LabelPattern:
    """
    Represents one alternative within a segment of lquery. For example, in 'foo*|bar@|baz%',
    there are 3 LabelPattern instances:
      - text='foo',   prefix=True,  case_insensitive=False, inword=False
      - text='bar',   prefix=False, case_insensitive=True,  inword=False
      - text='baz',   prefix=False, case_insensitive=False, inword=True
    """
    __slots__ = ("text", "prefix", "case_insensitive", "inword")

    def __init__(
        self,
        text: str,
        prefix: bool = False,
        case_insensitive: bool = False,
        inword: bool = False,
    ):
        self.text: str = text
        self.prefix: bool = prefix
        self.case_insensitive: bool = case_insensitive
        self.inword: bool = inword

    def matches(self, label: str) -> bool:
        """
        Returns True if `label` matches this pattern under the qualifiers.
        """
        # Apply case‐insensitivity if requested
        if self.case_insensitive:
            lab = label.lower()
            pat = self.text.lower()
        else:
            lab = label
            pat = self.text

        # 'inword' means: split the label on underscores, see if any part starts with pat
        if self.inword:
            parts = lab.split("_")
            return any(part.startswith(pat) for part in parts)

        # 'prefix' means: label must start with pat
        if self.prefix:
            return lab.startswith(pat)

        # otherwise: full equality
        return lab == pat

# ───────────────────────────────────────────────────────────────────────────
#  SegmentPattern: one segment of the lquery (e.g. "*{1,2}", or "foo*{2}", or "!apple|banana@")
# ───────────────────────────────────────────────────────────────────────────
class SegmentPattern:
    """
    Represents one “segment” (between dots) of an lquery. There are two broad cases:
      - is_wildcard=True:
          this segment is something like '*', '*{n}', '*{n,}', '*{n,m}', or '*{,m}'
          → it can match a variable number of labels.
      - is_wildcard=False (literal‐pattern):
          a segment that matches one or more consecutive labels, each tested
          against a list of LabelPattern(s), possibly negated, and possibly repeated
          (via {min,max} on a literal).

    Attributes (wildcard case):
      - is_wildcard: True
      - wild_min, wild_max: how many labels '*' can consume

    Attributes (literal case):
      - is_wildcard: False
      - negated: if True, we invert the meaning of the LabelPattern set
      - repeat_min, repeat_max: how many consecutive labels this segment can cover
      - alternatives: List[LabelPattern]

    Note: wild_max or repeat_max == math.inf means “no upper bound”.
    """

    __slots__ = (
        "is_wildcard",
        "wild_min",
        "wild_max",
        "negated",
        "repeat_min",
        "repeat_max",
        "alternatives",
    )

    def __init__(
        self,
        *,
        is_wildcard: bool,
        wild_min: int = 0,
        wild_max: int = math.inf,
        negated: bool = False,
        repeat_min: int = 1,
        repeat_max: int = 1,
        alternatives: Optional[List[LabelPattern]] = None,
    ):
        self.is_wildcard: bool = is_wildcard
        if self.is_wildcard:
            self.wild_min: int = wild_min
            self.wild_max: Union[int, float] = wild_max
            # the rest unused
            self.negated = False
            self.repeat_min = 0
            self.repeat_max = 0
            self.alternatives = []
        else:
            self.negated: bool = negated
            self.repeat_min: int = repeat_min
            self.repeat_max: Union[int, float] = repeat_max
            self.alternatives: List[LabelPattern] = alternatives if alternatives else []
            self.wild_min = 0
            self.wild_max = 0

    def __repr__(self) -> str:
        if self.is_wildcard:
            return f"<SegmentPattern WILDCARD{{{self.wild_min},{self.wild_max}}}>"
        neg = "!" if self.negated else ""
        alts = "|".join(
            (
                f"{p.text}"
                + ("*" if p.prefix else "")
                + ("%" if p.inword else "")
                + ("@" if p.case_insensitive else "")
                for p in self.alternatives
            )
        )
        if self.repeat_min == self.repeat_max:
            rep = f"{{{self.repeat_min}}}" if self.repeat_min != 1 else ""
        else:
            hi = "" if self.repeat_max is math.inf else str(self.repeat_max)
            rep = f"{{{self.repeat_min},{hi}}}"
        return f"<SegmentPattern {neg}{alts}{rep}>"

# ───────────────────────────────────────────────────────────────────────────
#  TreeDict: the enhanced in‐memory ltree store
# ───────────────────────────────────────────────────────────────────────────
class TreeDict:
    """
    In‐memory “ltree” store. Internally, each node’s key is stored as a tuple of labels,
    e.g. ("a","b","c"), and the value can be any JSON‐serializable Python object.
    This class supports:
      - set_node(path, value):  exact insertion/update by path
      - get_node(path):         exact lookup
      - delete_node(path, subtree=False):  delete one node or an entire subtree
      - query_nodes(pattern):   full Postgres‐style lquery (see :contentReference[oaicite:1]{index=1})
      - to_postgres(dsn, table_name):  dump all entries into a new Postgres table
      - classmethod from_postgres(dsn, table_name)           (rebuild from a Postgres table)
    """

    def __init__(self) -> None:
        # flat dict: key = tuple of labels, value = arbitrary Python object
        self._data: Dict[Tuple[str, ...], Any] = {}

    # ─────────────────────────────────────────────────────────────────────────
    #  Internal helpers: path normalization + lquery parsing
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _normalize_path(path: PathType) -> Tuple[str, ...]:
        """
        Convert a user‐provided path into a tuple of labels.
        Accepts:
          - dotted string: "a.b.c"
          - list of str: ["a","b","c"]
          - tuple of str: ("a","b","c")
        Raises ValueError if any segment is empty.
        """
        if isinstance(path, str):
            segments = path.split(".")
        elif isinstance(path, (list, tuple)):
            segments = list(path)
        else:
            raise ValueError(f"Unsupported path type: {type(path)}")

        if any((not seg) for seg in segments):
            raise ValueError(f"Empty label found in path: {segments!r}")
        return tuple(segments)

    @staticmethod
    def _parse_lquery(pattern: str) -> List[SegmentPattern]:
        """
        Parse a full Postgres lquery string (e.g. "Top.*{0,2}.sport*@.!football|tennis{1,}.Russ*|Spain")
        into a list of SegmentPattern objects. Refer to:
          • :contentReference[oaicite:2]{index=2}
        """

        def parse_wildcard_segment(raw: str) -> Optional[SegmentPattern]:
            """
            Check if raw is a '*' wildcard with optional {n,m} quantifier.
            E.g. "*", "*{2}", "*{1,}", "*{0,3}", "*{,4}"
            Returns a wildcard SegmentPattern or None.
            """
            m = re.fullmatch(r"\*(?:\{(\d*),?(\d*)\})?", raw)
            if not m:
                return None
            inner = m.group(1), m.group(2)  # (min_str, max_str) or (None,None) if no braces
            if inner == (None, None):
                # plain '*': matches 0..∞ labels
                return SegmentPattern(is_wildcard=True, wild_min=0, wild_max=math.inf)
            # has braces
            min_s, max_s = inner
            if min_s == "" and max_s != "":
                # "{,m}" → min=0, max=m
                wm_min = 0
                wm_max = int(max_s)
            elif max_s == "" and min_s != "":
                # "{n,}" → min=n, max=∞
                wm_min = int(min_s)
                wm_max = math.inf
            elif max_s is None and min_s is not None:
                # "{n}" → min=n, max=n
                wm_min = int(min_s)
                wm_max = int(min_s)
            else:
                # "{n,m}"
                wm_min = int(min_s) if min_s else 0
                wm_max = int(max_s) if max_s else math.inf
            return SegmentPattern(is_wildcard=True, wild_min=wm_min, wild_max=wm_max)

        def parse_literal_segment(raw: str) -> SegmentPattern:
            """
            Parse a “literal” segment, i.e. NOT a pure '*' wildcard. It may begin with '!'
            for negation, and/or end with '{n}', '{n,}', '{n,m}', '{,m}' to repeat the
            literal match. Inside, labels can be separated by '|' (OR).
            Each alternative may end with suffixes among '*', '@', '%' (any order).
            """

            negated = False
            if raw.startswith("!"):
                negated = True
                raw = raw[1:]  # strip the leading '!'

            # Check for a repetition quantifier {n}, {n,}, {n,m}, {,m}
            rep_min = rep_max = 1
            rep_match = re.fullmatch(r"(.*)\{(\d*),?(\d*)\}", raw)
            if rep_match:
                base = rep_match.group(1)
                min_s, max_s = rep_match.group(2), rep_match.group(3)
                if max_s == "" and "," in raw:
                    # e.g. "{n,}" or "{,m}"
                    if min_s == "":
                        # "{,m}" → 0..m
                        rep_min = 0
                        rep_max = int(max_s)
                    else:
                        # "{n,}" → n..∞
                        rep_min = int(min_s)
                        rep_max = math.inf
                elif max_s == "" and "," not in raw:
                    # "{n}" with no comma
                    rep_min = int(min_s)
                    rep_max = int(min_s)
                else:
                    # "{n,m}"
                    rep_min = int(min_s) if min_s else 0
                    rep_max = int(max_s) if max_s else math.inf
                raw = base  # remove the quantifier
            else:
                # no repetition → exactly 1
                rep_min = rep_max = 1

            # Now raw contains something like "foo*", "bar@", "baz%|qux", etc.
            alts: List[LabelPattern] = []
            for alt_raw in raw.split("|"):
                # For each alternative, strip suffix chars in {*, @, %}
                prefix = False
                case_ins = False
                inword = False
                txt = alt_raw

                # repeatedly strip any of "*", "@", "%" from end
                while txt and txt[-1] in ("*", "@", "%"):
                    ch = txt[-1]
                    if ch == "*":
                        prefix = True
                    elif ch == "@":
                        case_ins = True
                    elif ch == "%":
                        inword = True
                    txt = txt[:-1]

                if not txt:
                    raise ValueError(f"Invalid lquery alternative: '{alt_raw}'")

                alts.append(
                    LabelPattern(
                        text=txt, prefix=prefix, case_insensitive=case_ins, inword=inword
                    )
                )

            return SegmentPattern(
                is_wildcard=False,
                negated=negated,
                repeat_min=rep_min,
                repeat_max=rep_max,
                alternatives=alts,
            )

        segments: List[SegmentPattern] = []
        raw_segs = pattern.split(".")

        for raw in raw_segs:
            if not raw:
                raise ValueError(f"Empty lquery segment in pattern: {pattern!r}")
            wc = parse_wildcard_segment(raw)
            if wc is not None:
                segments.append(wc)
            else:
                segments.append(parse_literal_segment(raw))
        return segments

    # ─────────────────────────────────────────────────────────────────────────
    #  Matching engine: given a key (tuple of labels) and a parsed lquery, decide if they match
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _match_key_against(
        key_labels: Tuple[str, ...], pat_segs: List[SegmentPattern]
    ) -> bool:
        """
        Return True if the key (tuple of labels) matches the lquery (parsed as pat_segs).
        We use a recursive (backtracking) approach:
          - wildcard segments can skip 0..∞ labels
          - literal segments can consume repeat_min..repeat_max consecutive labels,
            each tested by the alternative LabelPattern set (with negation if requested).
        """

        # Memoization cache (i, j) → bool to avoid exponential blowup
        cache: Dict[Tuple[int, int], bool] = {}

        def dfs(i: int, j: int) -> bool:
            """
            Try to match pat_segs[j:] to key_labels[i:].
            Return True if rest matches exactly.
            """
            if (i, j) in cache:
                return cache[(i, j)]
            # If we've consumed all pattern segments:
            if j == len(pat_segs):
                # match only if also consumed all key labels
                res = i == len(key_labels)
                cache[(i, j)] = res
                return res

            seg = pat_segs[j]

            # Case 1: wildcard segment
            if seg.is_wildcard:
                # try consuming k labels, where k in [wild_min .. wild_max]
                low = seg.wild_min
                high = seg.wild_max if seg.wild_max is not math.inf else len(key_labels) - i
                # but k cannot exceed what's left
                high = min(high, len(key_labels) - i)
                for k in range(low, high + 1):
                    if dfs(i + k, j + 1):
                        cache[(i, j)] = True
                        return True
                cache[(i, j)] = False
                return False

            # Case 2: literal segment (with repetition)
            # We need to match rep consecutive labels at key_labels[i : i+rep] where rep in [repeat_min .. repeat_max].
            low = seg.repeat_min
            high = seg.repeat_max if seg.repeat_max is not math.inf else len(key_labels) - i
            high = min(high, len(key_labels) - i)

            for rep in range(low, high + 1):
                # check if key_labels[i : i+rep] all match (or all do NOT match if negated)
                ok = True
                for t in range(rep):
                    lbl = key_labels[i + t]
                    # check if any alternative matches
                    match_any = any(alt.matches(lbl) for alt in seg.alternatives)
                    if seg.negated:
                        if match_any:
                            ok = False
                            break
                    else:
                        if not match_any:
                            ok = False
                            break
                if not ok:
                    continue
                # if consumed rep labels successfully, recurse
                if dfs(i + rep, j + 1):
                    cache[(i, j)] = True
                    return True

            cache[(i, j)] = False
            return False

        return dfs(0, 0)

    # ─────────────────────────────────────────────────────────────────────────
    #  Public methods: set/get/delete/query
    # ─────────────────────────────────────────────────────────────────────────
    def set_node(self, path: PathType, value: Any) -> None:
        """
        Insert or overwrite the node at `path` (exact match) with `value`.
        """
        key = self._normalize_path(path)
        self._data[key] = value

    def get_node(self, path: PathType) -> Optional[Any]:
        """
        Return the value stored exactly at `path`, or None if missing.
        """
        key = self._normalize_path(path)
        return self._data.get(key)

    def delete_node(self, path: PathType, subtree: bool = False) -> int:
        """
        Delete the node at `path`. If subtree=True, also remove all descendants
        (any key that has `path` as a prefix).
        Returns the number of keys removed.
        """
        key = self._normalize_path(path)
        removed = 0

        if not subtree:
            if key in self._data:
                del self._data[key]
                return 1
            else:
                return 0

        # subtree=True: remove everything whose prefix == key
        to_delete = [k for k in self._data if k[: len(key)] == key]
        for k in to_delete:
            del self._data[k]
            removed += 1
        return removed

    def query_nodes(self, pattern: str) -> List[Tuple[str, Any]]:
        """
        Return a list of (dotted_path, value) for every node whose key matches
        the full Postgres‐style lquery `pattern`.
        See: :contentReference[oaicite:3]{index=3}.
        """
        pat_segs = self._parse_lquery(pattern)
        results: List[Tuple[str, Any]] = []

        for key_tuple, val in self._data.items():
            if self._match_key_against(key_tuple, pat_segs):
                dotted = ".".join(key_tuple)
                results.append((dotted, val))

        return results

    def all_paths(self) -> List[str]:
        """
        Return a sorted list of all stored paths (as dotted strings).
        """
        return sorted(".".join(k) for k in self._data.keys())

    def __len__(self) -> int:
        """
        Number of stored nodes.
        """
        return len(self._data)

    # ─────────────────────────────────────────────────────────────────────────
    #  Export to Postgres / Import from Postgres
    # ─────────────────────────────────────────────────────────────────────────
    def to_postgres(self, dsn: str, table_name: str) -> None:
        """
        Create (or replace) a new Postgres table called `table_name` with:
            id   SERIAL PRIMARY KEY,
            path ltree NOT NULL UNIQUE,
            data jsonb NOT NULL
        plus a GIST index on `path`, then bulk‐insert all in‐memory nodes.

        Args:
          - dsn: psycopg2 DSN string, e.g. "dbname=xxx user=yyy password=zzz host=... port=5432"
          - table_name: name of the new table to create
        """
        schema_sql = f"""
        CREATE EXTENSION IF NOT EXISTS ltree;

        DROP TABLE IF EXISTS {table_name} CASCADE;
        CREATE TABLE {table_name} (
            id   SERIAL PRIMARY KEY,
            path ltree        NOT NULL UNIQUE,
            data JSONB        NOT NULL
        );
        CREATE INDEX idx_{table_name}_path ON {table_name} USING GIST (path);
        """

        conn = psycopg2.connect(dsn, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(schema_sql)

        # Now bulk‐insert all key/value pairs
        insert_sql = f"INSERT INTO {table_name} (path, data) VALUES %s"
        values: List[Tuple[str, psycopg2.extras.Json]] = []
        for key_tuple, val in self._data.items():
            dotted = ".".join(key_tuple)
            values.append((dotted, psycopg2.extras.Json(val)))

        if values:
            with conn.cursor() as cur:
                psycopg2.extras.execute_values(
                    cur,
                    insert_sql,
                    values,
                    template="(%s, %s::jsonb)",
                    page_size=1000,
                )
        conn.close()

    @classmethod
    def from_postgres(cls, dsn: str, table_name: str) -> "TreeDict":
        """
        Read all rows from an existing table (created by to_postgres) with columns:
            path ltree, data jsonb
        and return a new TreeDict populated with those entries.

        Args:
          - dsn: psycopg2 DSN string
          - table_name: the existing table name (must have 'path' & 'data')
        """
        inst = cls()
        conn = psycopg2.connect(dsn, cursor_factory=psycopg2.extras.RealDictCursor)
        with conn.cursor() as cur:
            cur.execute(f"SELECT path::text AS p, data FROM {table_name};")
            rows = cur.fetchall()
            for row in rows:
                # split "a.b.c" → ["a","b","c"]
                labels = tuple(row["p"].split("."))
                inst._data[labels] = row["data"]
        conn.close()
        return inst
