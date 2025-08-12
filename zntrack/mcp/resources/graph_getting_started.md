```python
import zntrack
from package import Node1, Node2

project = zntrack.Project()

with project:
    node1 = Node1(param="value1")
    node2 = Node2(input=node1.output)

if __name__ == "__main__":
    project.build()
```
