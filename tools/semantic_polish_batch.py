from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EN_DIR = ROOT / "English"

PAIR_RE = re.compile(r'^"(?P<lhs>(?:[^"\\]|\\.)*)"\s*=>\s*"(?P<rhs>(?:[^"\\]|\\.)*)"\s*$')


def replace_pairs(path: Path, mapping: dict[str, str]) -> int:
    changed = 0
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    for line in lines:
        m = PAIR_RE.match(line)
        if not m:
            out.append(line)
            continue
        lhs = m.group('lhs')
        rhs = m.group('rhs')
        # Unescape for safe comparison
        key = lhs.encode('utf-8').decode('utf-8')
        if key in mapping:
            new_rhs = mapping[key]
            if new_rhs != rhs:
                changed += 1
            out.append(f'"{lhs}" => "{new_rhs}"')
        else:
            out.append(line)
    if changed:
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return changed


def main():
    total = 0
    # Babcia_Arrival semantic polish (initial segment)
    babcia_map = {
        "Bort med tassarna!": "Hands off 别碰",
        "God kväll. Är det här Hotel Devotchka?": "Good evening. Is this the Hotel Devotchka  晚上好，这里是 Devotchka 酒店吗？",
        "Det stämmer": "That's right 对",
        "Jag tror att jag ska bo här...": "I think I'm supposed to stay here 我想我应该住在这里……",
        "Jag heter Sebastian": "My name is Sebastian 我叫 Sebastian",
        "Hejsan, jag skulle vilja checka in": "Hello, I'd like to check in 你好，我想办理入住",
        "Jaha": "I see 我明白",
        "Jag heter Sebastian och jag vill checka in här": "My name is Sebastian and I'd like to check in here 我叫 Sebastian，我想在这里办理入住",
        "Lugn i stormen! En sekund": "Hold your horses! One second 别急，稍等一下",
        "Hur var namnet?": "What's your name 您叫什么名字？",
        "Sebastian": "Sebastian",
        "Sebastian...": "Sebastian...",
        "Sebbe": "Seb",
        "OK": "OK 好",
        "Låt mig kolla i datorn...": "Let me check the computer 我查一下电脑",
        "Här har vi dig ja. Bokad av Wellspring Soda AB?": "There you are. Booked by Wellspring Soda Inc  找到了，由 Wellspring Soda 公司预订的？",
        "Ja precis!": "Yes, exactly 是的，没错",
        "Mm, jo men så heter de nog": "Mhm, yes, I think that's what they're called 嗯，是的，我想是这个名字",
        "Det blir 499 kronor": "That'll be 499 kronor 需要 499 克朗",
        "Va?": "What 什么？",
        "Några problem?!": "Any problems  有什么问题？！",
        "Jag trodde allt var betalat av mitt företag?": "I thought everything was paid by my employer 我以为公司已经付过钱了？",
        "Jodå. Men det här är en depositionsavgift i händelse av förstörda föremål": "Yes. But this is a security deposit in case of damages to hotel property 是的，但这是押金，以防损坏酒店财物",
        "Eh, tar ni kort?": "Uh, do you take cards 呃，可以刷卡吗？",
        "Vi tar endast kort": "We only accept cards 我们只收信用卡",
        "OK, jag tror att jag har mitt kort här någonstans...": "OK, I think my card is here somewhere 好，我的卡应该就在这附近……",
        "Nej, det var inget": "No, never mind 不用了，算了",
        "Ni har väl kreditkort?": "You do have a credit card, right 你有信用卡吧？",
        "Eh... jadå det tror jag": "Uh... yeah, I think so 呃，是的，我想有",
        "OK, jag ska bara ta fram mitt kort...": "OK, I'll just get my card 好，我去把卡拿出来",
        "Undrar var jag lagt det...": "Wonder where I put it 不知道我把它放哪了……",
        "Kanske i väskan..?": "Maybe in the bag 也许在包里？",
        "Kreditkortet sa jag...": "The credit card, I said 我说的是信用卡……",
        "Hmm, jag tror att jag måste ha tappat det...": "Hmm, I think I must have lost it 嗯，我可能把它弄丢了……",
        "Det verkar tyvärr som att jag har blivit av med mitt kort": "Unfortunately, it seems I've lost my card 不巧，我的卡好像丢了",
        "Jaha?": "Yes 是吗？",
        "Det finns ingen möjlighet att skriva upp det på rummet eller så?": "Could you put it on my room bill 能先记在房账上吗？",
        "Jo det kan vi nog ordna": "Yes, we can probably arrange that 可以，问题不大",
        "Vissa administrativa avgifter tillkommer givetvis": "Of course, some administrative fees apply 当然，会收取一些管理费",
        "OK...": "OK... 好……",
        "Du får återkomma snarast när du har hittat kortet": "Come back as soon as you've found the card 找到卡后尽快回来办理",
        "Ja, det ska jag!": "Yes, I will 好的，我会的",
        # second OK lines will be handled if matched
        "Jag får nog ta och gå och leta rätt på det...": "I'd better go and look for it 那我先去找找",
        "Ja ja, gör så du": "Yes, do that 去吧",
        "Ja?": "Yes 嗯？",
        "Jag har kortet nu": "I have the card now 我找到卡了",
        "Jaha, kan man få se det?": "All right, may I see it 好的，我看看",
        "Eller vänta... nu hittar jag det inte igen": "Or wait... now I can't find it again 等等……我又找不到了",
        "Ehmmmm vad tusan": "Ehmmm, what the heck 呃……搞什么啊",
    }
    total += replace_pairs(EN_DIR / 'Babcia_Arrival.eng.mtf', babcia_map)
    # WellspringRepresentant_ShowingTheStorage semantic polish (head section)
    wr_map = {
        "Vart är du på väg?": "Where are you going 你要去哪？",
        "Kom med nu": "Come with me 跟我来",
        "Hallå?!": "Hello?! 喂？！",
        "Är du med?": "Are you with me 你跟上了吗？",
        "Förlåt, sa du något?": "Sorry, did you say something 抱歉，你刚说什么？",
        "Alltså, jag försöker komma på vem det är du liknar": "Um, I'm trying to figure out who you look like 嗯……我在想你像谁",
        "Det är någon skum skådis typ": "Like some oddball actor 有点像某个古怪的演员",
        "Hmm...": "Hmm... 嗯……",
        "Fan, jag kommer inte på det!": "Damn, I can't put my finger on it 糟了，我想不起来！",
        "Vet du vem det kan vara?": "Do you know who it might be 你知道可能是谁吗？",
        "Nå... jag vet inte riktigt": "Nah... I dunno 不太清楚",
        "Hmm inte direkt": "Hmm, not really 嗯，也不太像",
        "En del säger att jag är lik han i Seinfeldt": "Some people say that I look like that guy from Seinfeld 有人说我像《宋飞正传》里的那个人",
        "Är det en film eller?": "Is that a movie 那是电影吗？",
        "Nej men jag får tänka vidare på det...": "No, I'll have to keep thinking 不，回头我再想想",
        "Du är så jävla lik alltså!": "You're so damn alike 你简直像到爆！",
        "Helt sjukt": "That's crazy 太夸张了",
        "OK, så det här är datorn som kontrollerar dörren in i lagret.": "OK, so here's the computer that controls the warehouse door 好，这台电脑控制仓库的门",
        "Det är bara att skriva in 'unlock' och sedan lösenord så kan man gå genom dörren.": "Just enter 'unlock' and then the password 输入 'unlock'，再输入密码",
        "Fan, jävla skitkukdator!!!": "Damn it, this computer is a piece of shit!!! 该死，这破电脑！！！",
        "Vad är problemet?": "What's wrong 怎么了？",
        "Den här datorn styr dörren till lagret": "This computer controls the door to the warehouse 这台电脑控制仓库的门",
        "Men den accepterar inte mitt lösenord...": "But it won't accept my password 可它不接受我的密码……",
        "Ska jag försöka istället?": "Should I try instead 要不要我来试试？",
        "NEJ!": "NO! 不行！",
        "Eller kanske...": "Maybe... 也许吧……",
        "Kommer du inte in på datorn?": "You can't get into the computer 你进不去系统吗？",
        "Nej, du får försöka själv sen": "No, you'll have to try on your own later 不，等会你自己试试",
        "Verkar vara något fel med lösenordet": "Seems to be something wrong with the password 看来密码有问题",
        "Oj, jag måste dra snart": "Oh, I need to go soon 哦，我得走了",
        "Men först: den viktigaste regeln inom Wellspring!": "But first: the most important rule at Wellspring 但首先：Wellspring 最重要的一条规矩",
        "Tala ALDRIG illa om Wellspring och våra varumärken": "NEVER speak ill of Wellspring or our brands 绝对不要说 Wellspring 或我们品牌的坏话",
        "Naturligtvis": "Naturally 当然",
        "Jag förstår": "I understand 我明白",
        "Mm, OK...": "Mhm, OK 嗯，好",
        "Kan du den regeln så kommer nog allt att gå bra": "Know that rule and you'll do fine 记住这条规矩，你就没问题",
        "Sedan är det ju inte alla som har talang för att sälja": "And not everyone has the talent for selling 并不是每个人都擅长销售",
        "Nej, självklart": "No, of course 当然不是",
        "Jag tror att jag har lite talang i alla fall": "I think I have some talent at least 我觉得我多少还算有点天赋",
        "Hur vet man om man har talang?": "How do you know if you're talented 怎么确定自己有没有天赋？",
        "Det känner man": "You just feel it 自己能感觉到",
        "Men jag måste dra nu som som sagt": "But I have to go now, as I said 我得走了，先这样",
        "Lösenordet till datorn SKA vara abc123 om ingen har bytt": "The password SHOULD be abc123 unless someone changed it 密码应该是 abc123，除非被人改了",
        "Eller så var det 123abc": "Or maybe it was 123abc 或者 123abc",
        "123abc ?": "123abc ? 123abc？",
        "Ja, eller abc123": "Yeah, or abc123 对，abc123",
    }
    total += replace_pairs(EN_DIR / 'WellspringRepresentant_ShowingTheStorage.eng.mtf', wr_map)

    # Pixie_HackerTrial1 (intro segment)
    pht1_map = {
        "Va?": "What 什么？",
        "Vad gör du här?": "What are you doing here 你在这里做什么？",
        "Tänkte mest säga hej": "I was just gonna say hi 我就打个招呼",
        "Tja... jag vet inte riktigt": "Well, I don't really know 嗯……我也说不清",
        "Han har bett att få göra intagningsprovet": "He asked if he could take the trial 他想参加入会试炼",
        "Jag ska göra testet!": "I'm taking the test 我来参加测试",
        "OK..?!": "OK..?! OK..？！",
        "Jag sa ju att du inte ska följa efter mig!": "I told you not to follow me 我说过别跟着我！",
        "Lugn å fin nu, Pixie": "Take it easy, Pixie 冷静点，Pixie",
        "Han har bett om att få göra intagningsprovet": "He's asked to take the trial 他要参加试炼",
        "Jaha... ok?": "Oh... OK? 哦……好吧？",
        "Vänta nu": "Wait a sec 等一下",
        "Jag fattar typ ingenting": "I don't understand anything 我完全没听懂",
        "Så du vill börja jobba här med oss Sebastian?": "So you want to work here with us, Sebastian 你想来这儿和我们一起干，Sebastian？",
        "Eh, jo typ": "Uh, yeah, sorta 嗯，差不多吧",
        "Ja!": "Yes! 是！",
        "Det verkade så roligt": "It seemed like a lot of fun 看起来很有趣",
        "Men Yulian, han kom just till stan": "But Yulian, he just came to town 但是 Yulian，他才刚来这座城",
        "Han är försäljare, inte programmerare": "He's a salesman, not a programmer 他是销售，不是程序员",
        "Lugn Pixie, vi behöver alla vi kan komma över": "Easy, Pixie, we need everyone we can get 放轻松，Pixie，我们需要一切能用的人手",
        "Och han verkar ha tränat en del på egen hand, eller hur Sebastian?": "And he seems to have trained on his own, right, Sebastian 他看起来自己练过，对吧，Sebastian？",
        "Ja exakt": "Yeah, exactly 对，没错",
        "Mm... jag har en sån här modifierare också": "Mhm... I've got one of those modifiers, too 嗯……我也有这种修改器",
        "Typ": "Kinda 有点吧",
        "Ok, coolt... antar jag": "OK, cool... I guess 行吧，挺酷的……我想是",
        "Ja det blir riktigt bra det här": "I think this'll be great 我觉得这会很棒",
    }
    total += replace_pairs(EN_DIR / 'Pixie_HackerTrial1.eng.mtf', pht1_map)
    # Pixie_HackerTrial1 (follow-up requests for modifier)
    pht1_map_2 = {
        "Ska du gå och hämta den och komma tillbaka här sen?": "Will you go get it and come back 要去拿一下再回来吗？",
        "Mm, låter som en bra idé": "Yeah, sounds like a plan 嗯，听起来不错",
        "Jag väntar här så länge": "I'll wait here 我先在这等着",
        "Har du den nu?": "Do you have it now 现在拿到了吗？",
        "Ni har ingen jag kan få låna?": "Do you have one I can borrow 有能借我用一下的吗？",
        "Ska kolla...": "Lemme check 我看看",
        "Här!": "Here! 给",
        "Jag tror inte det tyvärr": "Don't think so, sorry 恐怕没有，抱歉",
        "Du får gå och leta rätt på den": "You'll have to go find it 你得自己去找找",
        "Bra": "Good 好",
        "OK, så såhär ligger det till": "OK, so this is how it works 好，事情是这样的",
    }
    total += replace_pairs(EN_DIR / 'Pixie_HackerTrial1.eng.mtf', pht1_map_2)

    # Hank_FirstLecture (intro/common lines)
    hfl_map = {
        "Kom över hit är du snäll": "Would you please come over here 请到这边来一下",
        "Ok, ska vi börja då?": "OK, shall we start 好的，我们开始吧",
        "Ok, visst": "OK, sure 好的，当然",
        "Jag väntar här så länge då": "I'll wait here then 我先在这等着",
        "Hallå där, då kör vi": "Hey, let's do this 开始吧",
        "Har testat din modifierare någonting förut?": "Have you tried your modifier yet 你之前用过修改器吗？",
        "Ja, lite": "Yeah, a bit 嗯，用过一点",
        "Ok, vad bra": "OK, that's good 好的，那很棒",
        "Har du förstått hur den fungerar?": "Have you figured out how it works 你弄明白它怎么工作了吗？",
        "Jodå, det var inte så svårt": "Sure, it wasn't that difficult 是的，不算难",
        "Njae... inte exakt": "Nah... not really 嗯……不太算",
        "Ok..?": "OK...? 好的……？",
        "Vad var det jag skulle göra?": "What was I supposed to do 我要做什么来着？",
        "Hacka den stora datorn här, den med ratten": "Hack the big one here, the one with the wheel 攻破这台大的，有个转轮的那台",
        "Ja, exakt!": "Just like that 没错，就是这样",
        "Såg du koden?": "Did you see the code 你看到代码了吗？",
        "Ok? Bra": "OK? Great 好吗？太好了",
        "Mm": "Mm 嗯",
        "Bra": "Nice 不错",
        "Grundprincipen är att du kopplar in din modifierare i ett föremål": "The basic principle is connecting your modifier to an object 基本原理是把修改器接到目标上",
        "Och sen får du se koden som det föremålet innehåller": "Then you can see that object's code 然后你就能看到它的代码",
        "Det är ju jättekonstigt!": "That's really weird 这也太奇怪了",
        "Vem kom på att man kunde göra så?": "Who came up with this idea 这是谁想到的？",
    }
    total += replace_pairs(EN_DIR / 'Hank_FirstLecture.eng.mtf', hfl_map)

    # _OnThePhone (menu/early)
    otp_map = {
        "PLAY GAME FROM THE BEGINNING": "PLAY GAME FROM THE BEGINNING 从头开始游戏",
        "Chapter 1 (first day)": "Chapter 1 (first day) 第一章（第一天）",
        "Chapter 2 (after dot)": "Chapter 2 (after dot) 第二章（俱乐部之后）",
        "Chapter 3 (tests)": "Chapter 3 (tests) 第三章（试炼）",
        "Chapter 4 (factory)": "Chapter 4 (factory) 第四章（工厂）",
        "Chapter 5 (experiment)": "Chapter 5 (experiment) 第五章（实验）",
        "Chapter 6 (final act)": "Chapter 6 (final act) 第六章（最终幕）",
    }
    total += replace_pairs(EN_DIR / '_OnThePhone.eng.mtf', otp_map)

    # Hank_SecondLecture (selected)
    hsl_map = {
        "Jo": "Yeah 嗯",
        "Ok": "OK 好的",
        "Bra": "Good 好",
    }
    total += replace_pairs(EN_DIR / 'Hank_SecondLecture.eng.mtf', hsl_map)

    print(f"Polished lines: {total}")


if __name__ == "__main__":
    main()
