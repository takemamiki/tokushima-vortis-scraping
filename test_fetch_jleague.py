from fetch_jleague import extract_payload, parse_match, parse_score_time

assert parse_score_time("28'") == (28, 0)
assert parse_score_time("90+2'") == (90, 2)
assert parse_score_time("45+1'") == (45, 1)

def load(match_id):
    with open(f"data/jleague_{match_id}.html", encoding="utf-8") as f:
        return parse_match(extract_payload(f.read()), match_id)


# 普通の試合
r = load("102412")
assert (r["home_score"], r["away_score"]) == (0, 1)
assert len(r["goals"]) == 1

# オウンゴール：得点が入ったチーム側に入っている
r = load("092613")
og = [g for g in r["goals"] if g["is_own_goal"] == 1]
assert len(og) == 1
assert og[0]["club"] == "徳島ヴォルティス"

# 0-0：得点者リストが空
r = load("101718")
assert r["goals"] == []

# アディショナルタイム・全角の正規化
r = load("101719")
assert r["away_club"] == "横浜FC"
assert any(g["minute"] == 90 and g["added_time"] == 6 for g in r["goals"])

print("全部OK")
