# Steal a Gobo (Scratch game)

A Scratch 3 game in the style of "Steal a Brainrot" / "Steal a Scratch Cat", but with Gobos.
Buy Gobos from the red carpet, keep them in your base so they make money, and press the
big STEAL button to sneak into another player's base and steal a Gobo.

## How to open it

1. Download `Steal_a_Gobo.sb3`.
2. Go to <https://scratch.mit.edu> and click **Create**.
3. Click **File → Load from your computer** and choose `Steal_a_Gobo.sb3`.
4. Click the green flag, then press **Space** to start.

## How to play

| Key | What it does |
| --- | --- |
| Arrow keys or W A S D | Walk |
| E or Space | Buy a Gobo on the carpet, or steal a Gobo in another player's base |
| X | Sell one of your Gobos (you get half the price back) |
| U | Buy faster shoes |
| R | Rebirth: start again with no Gobos, but every Gobo makes more money |
| Mouse click | Press the STEAL, SKINS, PETS and INVENTORY buttons, and things in the shops |
| X (mouse over a pet in INVENTORY) | Delete that pet |

- Gobos walk along the **red carpet**. Touch one and press **E** to buy it. It goes to **Your Base**.
- Every Gobo in your base makes money every second.
- Click the big **STEAL** button. You go into another player's base (Bob, Zara, Max or Luna)
  full of random Gobos.
- Touch one Gobo and press **E** to steal it. You can only steal **one**. Then you go straight
  back to the place you were before, and the Gobo goes into your base.
- You have 20 seconds in their base. If you are too slow, you go home with nothing.
- After you press STEAL, you must wait **1 minute 30 seconds** before you can steal again.
  The button turns grey and shows how many seconds are left.

## Gobo types

There are 24 Gobos. The rarer ones are harder to find on the carpet and in other players' bases.

| Gobo | Rarity | Price | Money per second |
| --- | --- | --- | --- |
| Gobo | Common | $10 | $1 |
| Bubblegum Gobo | Common | $15 | $2 |
| Honey Gobo | Common | $20 | $2 |
| Leaf Gobo | Uncommon | $50 | $4 |
| Choco Gobo | Uncommon | $80 | $6 |
| Cactus Gobo | Uncommon | $100 | $7 |
| Ice Gobo | Rare | $250 | $15 |
| Ocean Gobo | Rare | $400 | $22 |
| Candy Gobo | Rare | $550 | $28 |
| Fire Gobo | Epic | $1,200 | $60 |
| Ninja Gobo | Epic | $2,000 | $90 |
| Lava Gobo | Epic | $3,000 | $120 |
| Robo Gobo | Legendary | $6,000 | $250 |
| Pirate Gobo | Legendary | $9,000 | $350 |
| Moon Gobo | Legendary | $12,000 | $450 |
| Galaxy Gobo | Mythic | $25,000 | $900 |
| Ghost Gobo | Mythic | $40,000 | $1,300 |
| Thunder Gobo | Mythic | $55,000 | $1,700 |
| Golden Gobo | Gobo God | $120,000 | $3,500 |
| Diamond Gobo | Gobo God | $200,000 | $5,500 |
| Cyber Gobo | Gobo God | $300,000 | $7,500 |
| Rainbow Gobo | Secret | $600,000 | $15,000 |
| Dragon Gobo | Secret | $1,000,000 | $25,000 |
| Shadow Gobo | Secret | $2,000,000 | $45,000 |

## Skins

Click the purple **SKINS** button (top left) to open the Skin Shop. Click a skin to buy it with your
money. Click a skin you own to wear it. The skin you are wearing glows and wiggles. Click **BACK** to
return to the game.

| Skin | Price |
| --- | --- |
| Classic Thief | free |
| Red Robber | $100 |
| Green Sneak | $250 |
| Pink Bandit | $500 |
| Ninja | $1,000 |
| Pirate | $2,500 |
| Cowboy | $5,000 |
| Chef | $7,500 |
| Astronaut | $10,000 |
| Robot | $20,000 |
| Zombie | $30,000 |
| Wizard | $50,000 |
| Knight | $75,000 |
| Superhero | $100,000 |
| Clown | $150,000 |
| King | $250,000 |
| Gobo Suit | $400,000 |
| Alien | $600,000 |
| Golden Thief | $1,000,000 |
| Rainbow Legend | $2,500,000 |

## Pets

Click **PETS** (top left) to open the Pet Shop. Click a Lucky Block to buy it. It shakes, cracks and
breaks open into a random pet. Each block has its own 4 pets: the first one comes 45% of the time,
then 30%, 18%, and the best one only 7%.

Click **INVENTORY** to see your pets (up to 20). Click a pet to equip it (up to 3). Equipped pets follow
you around and give you a money boost: the numbers add up, so a +35% and a +50% pet give +85% money.
The **Pet Boost** box at the top shows your total boost. Hold the mouse over a pet and press **X** to
delete it.

| Lucky Block | Price | Pets inside (worst to best) |
| --- | --- | --- |
| Wood Lucky Block | $500 | Puppy (+5%), Kitten (+5%), Bunny (+8%), Hamster (+10%) |
| Iron Lucky Block | $5,000 | Fox (+15%), Owl (+18%), Penguin (+20%), Panda (+25%) |
| Gold Lucky Block | $50,000 | Lion (+35%), Tiger (+40%), Unicorn (+50%), Phoenix (+60%) |
| Diamond Lucky Block | $500,000 | Crystal Wolf (+80%), Ice Dragon (+100%), Robo Cat (+110%), Golden Eagle (+130%) |
| Rainbow Lucky Block | $5,000,000 | Rainbow Unicorn (+200%), Galaxy Whale (+250%), Gobo King (+300%), Cosmic Dragon (+400%) |

## Animations

Gobos wobble, blink and waddle along the carpet. Gobos in your base pop out coins, and Gobos in other
players' bases shiver when you come close. The thief walks with swinging legs, clouds float by, and
comic bursts (KA-CHING!, WOW!, SOLD!, ZOOM!) and full-screen flashes (SNEAK ATTACK!, YOINK!,
TOO SLOW!, REBIRTH!) pop up when things happen.

## Changing the game

`build_sb3.py` makes the `.sb3` file from code. Run `python3 build_sb3.py` to rebuild it.
You can also just open the game in Scratch and edit the blocks there.
