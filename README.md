# Welcome to Brainfunk!

> ### Note:
> The Replit no longer works due to changes in the Replit workspace. It's possible the Discord API might have changed in the past few years as well, I haven't checked.

## Putting the *fun* back into *Brainfuck*

[Brainfuck](https://wikipedia.org/wiki/Brainfuck) is an esoteric programming language with only 8 symbols: ` + - < > [ ] . , `  
This bot will interpret your Brainfuck code for you, right inside your favorite Discord server!

### Setting Up Brainfunk On Replit
1. You will need a Discord bot account
    - See the first 6 minutes of [this video](https://www.youtube.com/watch?v=SPTfmiYiuok) for instructions on getting a bot account set up and inviting it to a Discord server
2. Fork the [BrainfunkBot](https://replit.com/@quazillionaire/BrainfunkBot) repl, as well as the [BrainfuckAPI](https://replit.com/@quazillionaire/BrainfuckAPI) repl
3. In the bot repl, you need to make a couple small changes:
    1. Create a secret environment variable (lock icon on the left sidebar) with "token" as the key, and your Discord bot access token as the value
    2. In `main.py` on line 8, change the `USER` variable to your Replit username
4. Run both the API repl and the bot repl
5. Use `/bf help` for some tips. Enjoy!
