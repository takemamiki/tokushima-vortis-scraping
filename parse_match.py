"""
parse_match.py
fetch_match.py が取得したvortis.jpのHTMLから、スコア・チーム名・得点者を抜き出す。

役割：HTMLの中から欲しい情報だけを見つけて取り出すこと。
    サイトにアクセスするのは fetch_match.py の役目。
"""

from bs4 import BeautifulSoup

def get_scorers_and_minutes(score_div):
    """
    homeScore/awayScoreのdivから、得点者名と得点時間のリストを取り出す。
    無得点で<ul>が存在しない場合は空リストを返す。
    """
    scorers  = []
    minutes = []

    for li in score_div.find_all("li"):
        minute_tag = li.find("span")
        name_tag = li.find("span", class_="name")

        if minute_tag:
            minutes.append(minute_tag.get_text(strip=True))
        if name_tag:
            scorers.append(name_tag.get_text(strip=True))

    return scorers, minutes


def parse_match(html: str) -> dict:
    """
    試合結果ページのHTML文字列を受け取り、試合データを辞書で返す。
    """
    soup = BeautifulSoup(html, "html.parser")

    home_div = soup.find("div", class_="home")
    away_div = soup.find("div", class_="away")
    if home_div is None or away_div is None:
        raise ValueError("チーム名の場所が見つかりません（ページの中身が想定と違う可能性)")

    home_club = home_div.find("figcaption").get_text(strip=True)
    away_club = away_div.find("figcaption").get_text(strip=True)
   
    home_score_div = soup.find("div", class_="homeScore")
    away_score_div = soup.find("div", class_="awayScore")

    home_score = home_score_div.find("span", recursive=False).get_text(strip=True)
    away_score = away_score_div.find("span", recursive=False).get_text(strip=True)

    home_scorers, home_minutes = get_scorers_and_minutes(home_score_div)
    away_scorers, away_minutes = get_scorers_and_minutes(away_score_div)

    match_data = {
        "home_club": home_club,
        "away_club": away_club,
        "home_score": home_score,
        "away_score": away_score,
        "scorers": home_scorers + away_scorers,
        "minutes": home_minutes + away_minutes,
        }

    return match_data


if __name__== "__main__":
    with open("data/sample_vortis_match.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    match_data = parse_match(html)
    print(match_data)