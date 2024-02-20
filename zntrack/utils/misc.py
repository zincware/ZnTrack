from __future__ import annotations

import typing as t
if t.TYPE_CHECKING:
    from zntrack import Node

def get_init_msg(self: "Node") -> str|None:
    if self.citation() and self.license():
        return f"The content of '{self}' is licensed under {self.license()} and provides a citation."
    elif self.citation():
        # if only citation
        return f"The content of '{self}' provides a citation."
    elif self.license():
        # if only license
        return f"The content of '{self}' is licensed under {self.license()}."
    else:
        # if none
        return None
