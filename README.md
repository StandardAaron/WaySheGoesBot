# WaySheGoesBot

### This is WaySheGoesBot, affectionately known as 'Ray'. Ray likes VLTs, pepperoni, and liquor. 
### But mostly VLTs right now.

'Ray' is a Telegram bot that provides fun, no-stakes slot machine functionality with a Trailer Park Boys theme.

### FAQ

#### General
- Why a slot machine?

> For many years my team used Google Chat as our primary means of communication, and we came to rely on the built-in dice rolling feature (the video conference table-top gamer's secret weapon :) ) to decide many a random argument, as well as the "winner of the day" - a meaningless, yet highly coveted title.
Things changed over time, GChat went away, and people moved on, so Telegram was chosen as the platform to maintain contact. `/roll d100` eventually gave way to variations of Cee-lo/Craps `/roll 3d6`, and so a slot machine bot was just a natural progression of that.

> TL;DR: It's just something fun to pass the time.

- Why Trailer Park Boys?

> As a born and raised Nova Scotian, TPBs was just the recognized meme/quoteable export that others assumed (correctly) that I'd get, and vice versa. Immature, sure, but it has a certain charm, and it has kinda just stuck.

- What's a "VLT"?
    
> "VLT" stands for Video Lottery Terminal, and is very common TLA used on the East Coast.

- "WaySheGoesBot"?
    
> Yep. Because that is, in fact, the way she goes (with any game of chance - or life in general if you ask Ray).
>> " Sometimes she goes, sometimes she don't go; way she goes. "

#### Technical

- Where does this thing run?

> For the last year and a bit, Ray has run off my home workstation in polling mode. While this has served surprisingly well for our needs, there are some cases where downtime is unavoidable (not just due to host downtime, but also some odd behaviour of Telegram request throttling). Thus, the time has come to move the bot to a more capable and permanent home, most likely as a lambda service on AWS with accompanying webhooks, dynamoDB for state, etc. Stay tuned.

- How do you interface with Telegram?

> Ray is running Running off https://github.com/eternnoir/pyTelegramBotAPI, for no other reason than it was the library I had available through Fedora repos at the time, and because it did provide some useful and time saving abstractions over the Official Telegram API. As it turns out, this has served quite well and is reasonably well maintained.

- What else does this need to run?

> The bot uses basic standard library stuff other than the aforementioned Telegram API helper; Numpy and sqlite3, though the latter may go away in the future in favour of something else to save state.

- Can I add Ray to my group on Telegram?

> Sure, as long as you don't mind some light adult humour (I cleaned up the language for the most part) and potential downtime as I tinker around.

- Plans for the future?

> other moving to a hosted service? ... "WaySheGolangBot", maybe? :D
