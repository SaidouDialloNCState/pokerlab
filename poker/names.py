import random

FIRST = [
    "Ava","Liam","Mia","Noah","Zoey","Elijah","Ivy","Lucas","Luna","Mateo","Aria","Ethan","Nora","Logan","Emma",
    "Amir","Chloe","Zayn","Layla","Owen","Ruby","Ezra","Stella","Kai","Bella","Leo","Maya","Jack","Isla","Eli",
    "Aiden","Lila","Caleb","Hazel","Micah","Sofia","Jude","Alice","Evan","Naomi","Mark","Elena","Axel","Sarah",
    "Jason","Zara","Ian","Hana","Drew","Aisha","Miles","Yara","Felix","Nadia","Xavier","Amina","Omar","Siena",
    "Roman","Diana","Silas","Alina","Kian","Freya","Milan","Mara","Rory","Keira","Rafael","Tessa","Zeke","Cara",
    "Emil","Rhea","Noel","Skye","Joel","Piper","Nigel","Wren","Remy","Quinn","Colin","Evie","Orion","Mila",
    "Jonah","Elise","Zion","Clara","Rowan","Ada","Arlo","Esme","Nico","Iris"
]
LAST = [
    "Rivera","Nguyen","Patel","Kim","Singh","Thomas","Hernandez","Lopez","Khan","Carter","Wright","Green","Walker",
    "Young","Hall","Scott","Adams","Baker","Gonzalez","Perez","Roberts","Murphy","Cook","Rogers","Morgan","Reed",
    "Bailey","Cooper","Richardson","Cox","Ward","Diaz","Hughes","Flores","Sanchez","Perry","Butler","Russell",
    "Griffin","Bryant","Alexander","Hayes","Myers","Ford","Hamilton","Graham","Sullivan","Fisher","Castillo",
    "Romero","Murray","Medina","Bishop","Schmidt","Holt","Webb","Parker","Boone","Stone","Keller","Shaw",
    "Wheeler","Hardy","Hunter","Lawson","Wolfe","Barrett","Kaur","Chaudhry","Sharma","Mehta","Basu","Iyer",
    "Desai","Ghosh","Fernandez","Costa","Silva","Rossi","Ricci","Greco","Moretti","Conti","Marino","De Luca",
    "Mancini","Ferri","Esposito","Romano","Fiore","Valente","Sartori","Lombardi","Fontana"
]

def random_names(n: int, exclude=None):
    """Return n unique 'First Last' combos. First and last are chosen independently for a huge pool."""
    exclude = set(exclude or [])
    out = []
    used = set(exclude)
    tries = 0
    while len(out) < n and tries < 10000:
        tries += 1
        name = f"{random.choice(FIRST)} {random.choice(LAST)}"
        if name not in used:
            used.add(name)
            out.append(name)
    # Fallback with numbered names if somehow not enough
    i = 1
    while len(out) < n:
        cand = f"Player{i}"
        if cand not in used:
            used.add(cand)
            out.append(cand)
        i += 1
    return out
