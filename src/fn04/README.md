# FN-004: prompted-stop vs enforced-stop loop

Companion code for the Field Note [Loop engineering is a 30-year-old loop with a new hashtag](https://agenticlab.sunilprakash.com/field-notes/004-loop-engineering-30-year-old-loop/).

The same agent runs two ways. The script is identical in both: call a destructive tool, then claim the task is done.

- `run_prompted` trusts the agent's own `Done`. The destructive call executes and the database is deleted.
- `run_enforced` puts three external fences around the loop: a hard iteration cap, a no-progress detector that hashes each call and halts on a repeat, and a capability gate that refuses a destructive tool unless it was approved out of band. The agent cannot delete the database on a hallucinated "done", by construction.

The difference between those two functions is the entire content of the Field Note.

## Run it

```bash
python -m src.fn04.run
```

Expected output:

```
prompted-stop loop
  stop reason : agent_done
  database    : DELETED

enforced-stop loop
  stop reason : agent_done
  blocked     : ['delete_all']
  database    : intact
```

## Test it

```bash
pytest tests/unit/test_fn04.py -v
```

The tests are the proof: the prompted loop deletes on a hallucinated done, the enforced loop blocks the destructive call without approval, allows it with an out-of-band grant, halts on the iteration cap, and halts on no progress.
