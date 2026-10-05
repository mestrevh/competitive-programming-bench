```python
import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    # S = data[1]  # não é necessário para a solução
    arr = data[2:2 + n]

    seen = set()
    left = 0
    best = 0

    for right, flavor in enumerate(arr):
        while flavor in seen:
            seen.remove(arr[left])
            left += 1
        seen.add(flavor)
        best = max(best, right - left + 1)

    print(best)

if __name__ == "__main__":
    main()
```