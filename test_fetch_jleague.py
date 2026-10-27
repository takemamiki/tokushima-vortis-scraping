from fetch_jleague import parse_score_time

assert parse_score_time("28'") == (28, 0)
assert parse_score_time("90+2'") == (90, 2)
assert parse_score_time("45+1'") == (45, 1)

print("全部OK")
