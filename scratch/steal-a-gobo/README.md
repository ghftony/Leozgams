# Steal a Gobo (Scratch game)

A Scratch 3 game. Sneak into the Gobo Vault, grab a Gobo, and run back to your base
before the Guard catches you. Every Gobo in your base makes money each second.

## How to open it

1. Download `Steal_a_Gobo.sb3`.
2. Go to <https://scratch.mit.edu> and click **Create**.
3. Click **File → Load from your computer** and choose `Steal_a_Gobo.sb3`.
4. Click the green flag, then press **Space** to start.

## How to play

- **Arrow keys** or **W A S D**: move the thief.
- Touch a Gobo in the red **Gobo Vault** to grab it (the Guard will chase you!).
- Carry it into the blue **Your Base** to keep it.
- Gobo types: yellow Gobo = $2/s, Gold Gobo = $10/s, Diamond Gobo = $50/s (rare).
- Press **U** to buy more speed (the price doubles each time).
- The Guard gets faster as you steal more Gobos. You have 3 lives.
- Reach **$1000** to win.

## Changing the game

`build_sb3.py` makes the `.sb3` file from code. Run `python3 build_sb3.py` to rebuild it.
You can also just open the game in Scratch and edit the blocks there.
