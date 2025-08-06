```python
import zntrack
from package import Node1, Node2

project = zntrack.Project()

with zntrack.group("group1"):
    node1 = Node1(param="value1")

with zntrack.group("group2"):
    node2 = Node2(input=node1.output)

with project.group("group1", "nested"):
    node3 = Node1(param="value2")

if __name__ == "__main__":
    project.build()
```