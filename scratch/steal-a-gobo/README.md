# Steal a Gobo (Scratch game)

A Scratch 3 game in the style of "Steal a Brainrot" / "Steal a Scratch Cat", but with Gobos.
Buy Gobos from the red carpet, keep them in your base so they make money, steal Gobos
from the Rival's base, and stop the Rival from stealing yours.

## How to open it

1. Download `Steal_a_Gobo.sb3`.
2. Go to <https://scratch.mit.edu> and click **Create**.
3. Click **File → Load from your computer** and choose `Steal_a_Gobo.sb3`.
4. Click the green flag, then press **Space** to start.

## How to play

| Key | What it does |
| --- | --- |
| Arrow keys or W A S D | Walk |
| E or Space | Buy a Gobo on the carpet, or steal a Gobo from the Rival Base |
| X | Sell one of your Gobos (you get half the price back) |
| U | Buy faster shoes |
| R | Rebirth: start again with no Gobos, but every Gobo makes more money |

- Gobos walk along the **red carpet**. Touch one and press **E** to buy it. It goes to **Your Base**.
- Every Gobo in your base makes money every second.
- Walk into the **Rival Base**, touch a Gobo and press **E** to steal it. Run back to your base!
  If the Rival catches you, he takes it back.
- The Rival also comes to steal your best Gobo. Touch him to get it back.
- Step on the green **LOCK** button to put lasers on your base for 25 seconds.
  Sometimes the Rival locks his base too.

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
