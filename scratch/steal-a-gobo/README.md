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
| Mouse click | Press the STEAL button |

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

| Gobo | Rarity | Price | Money per second |
| --- | --- | --- | --- |
| Gobo | Common | $10 | $1 |
| Leaf Gobo | Rare | $60 | $5 |
| Ice Gobo | Epic | $300 | $20 |
| Fire Gobo | Legendary | $1,500 | $80 |
| Galaxy Gobo | Mythic | $7,500 | $350 |
| Golden Gobo | Gobo God | $30,000 | $1,500 |
| Rainbow Gobo | Secret | $150,000 | $7,000 |

## Changing the game

`build_sb3.py` makes the `.sb3` file from code. Run `python3 build_sb3.py` to rebuild it.
You can also just open the game in Scratch and edit the blocks there.
