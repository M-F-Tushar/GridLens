"""
The domain layer is like a set of official forms and rules.

It says:

“This is what a valid request looks like, and this is what a valid answer looks like.”

It does not do the actual work. It only makes sure that the information being passed around is organized and valid.

Everything in this package is pure data (Pydantic models). No I/O, no
network calls, no LLM calls happen here. This keeps the numerical core of
GridLens fully deterministic and independent of any AI provider.

"""