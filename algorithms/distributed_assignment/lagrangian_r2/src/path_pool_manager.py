"""Deterministic path storage; no reference-solution inputs."""


class PathPool:
    def __init__(self, commodity_count, limit):
        self.paths = [[] for _ in range(commodity_count)]
        self.seen = [set() for _ in range(commodity_count)]
        self.limit = limit
        self.events = []

    def add(self, commodity, path, iteration, source="capacity_priced_shortest_path"):
        key = tuple(path)
        if key in self.seen[commodity]:
            return False
        if len(self.paths[commodity]) >= self.limit:
            return False
        self.seen[commodity].add(key)
        self.paths[commodity].append(key)
        self.events.append((iteration, commodity, source, key))
        return True

    def count(self):
        return sum(map(len, self.paths))
