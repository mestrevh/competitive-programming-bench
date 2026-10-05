```python
import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    # data[1] is S, but it is not needed for the solution
    arr = data[2:2 + n]

    last = {}          # last position where each flavor was seen
    left = 0
    max_len = 0

    for right, flavor in enumerate(arr):
        if flavor in last and last[flavor] >= left:
            left = last[flavor] + 1
        last[flavor] = right
        max_len = max(max_len, right - left + 1)

    print(max_len)

if __name__ == "__main__":
    main()
```