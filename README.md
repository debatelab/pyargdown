# pyargdown

A simple [Argdown](https://argdown.org) parser written in Python and based on Lark.

Install:

```
pip install "git+https://github.com/debatelab/pyargdown"
```

Use:

```python
import pyargdown as agd

snippet = """\
[Claim A]
    + <Reason 1>
    - <Reason 2>
                                
<Reason 1>

(1) Premise 1.
-----
(2) [Claim B]: Conclusion.
"""

argdown = agd.parse_argdown(snippet)
assert isinstance(argdown, agd.ArgdownMultiDiGraph)
```
