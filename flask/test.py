s="The best model improves the baseline by -30.41%.\nMovies recommended for you(用户ID：推荐电影ID：推荐分数：推荐电影名称):\n1:2574:5.8246170779602595:「冷静と情熱のあいだ」オリジナルサウンドトラック (2001)\n1:2334:5.206385970313846:Cry Freedom: Original Motion Picture Soundtrack (1990)\n1:1857:5.103226007781355:张学友:等你等到我心痛 (1993)\n1:1650:5.084588001285728:This Is The One (2009)\n1:1387:5.034029152937491:岛国之情歌(Vol.1)再见我的爱人 (1975)\n2:1377:5.7359314054575306:十二楼的莫文蔚 (2000)\n2:171:5.66869656185399:Brahms: 4 Symphonien, Etc / Sanderling, Berlin SO (1992)\n2:4222:5.640898499642069:Girotondo (2010)\n2:1904:5.640730940672908:111 Classics For Christmas (NULL)\n2:2415:5.578017387386446:Angels & Demons (2009)\n3:3306:5.393882641686657:Appetite For Destruction (1987)\n3:3707:5.279984288902208:生活倒影 (2018)\n3:4119:5.171616725860665:With the Beatles (1963)\n3:182:5.100085993608525:Anyone But You (Original Motion Picture Soundtrack) (2023)\n3:2615:5.026638810456253:有生之年 (2024)\n4:3048:5.820676248418397:Tous Les Matins du Monde (2002)\n4:581:5.537638539364878:ブルーバード (2008)\n4:1954:5.397273178312424:Schubert: The Late Piano Sonatas D 958, 959 & 960; 3 Piano Pieces D 946; Allegretto D 915 (2004)\n4:3926:5.309177543688479:Saxophonic (2003)\n4:3648:5.292734817423792:Cowboys From Hell (1990)\n"

def split_stdout(s:str)->list[str]:
    lines=s.split("\n")
    res=[]
    for i in range(2,len(lines)):
        word=lines[i].split(":")
        if len(word)>2:
            res.append({'user_id':word[0],'movie_id':word[1],'rating':word[2],'name':word[3]})
    return res

print(split_stdout(s))