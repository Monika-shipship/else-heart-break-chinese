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

    print(f"Polished lines: {total}")


if __name__ == "__main__":
    main()

