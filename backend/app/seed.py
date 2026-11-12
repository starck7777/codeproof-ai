from . import store
from .catalog import STRATEGIES
from .db import Base, engine


def main():
    Base.metadata.create_all(engine)
    for strategy in STRATEGIES:
        identity = "seed-" + strategy
        if not store.get(identity):
            store.save(
                identity,
                "agent",
                {
                    "id": identity,
                    "kind": "agent",
                    "name": strategy + " Agent",
                    "strategy": strategy,
                    "model": "openai/gpt-4o-mini",
                    "version": 1,
                },
            )


if __name__ == "__main__":
    main()
