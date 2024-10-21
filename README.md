### Join The Discord Server to use this bot!!
- free to use and always online!*
  [https://discord.gg/fHfmjaCXtb](https://discord.gg/k5NeWuxAU6)
  
## Purposes
- Resign encrypted saves (both with or without replacing the decrypted contents, also known as encrypting)
- Decrypt encrypted saves
- Re-region encrypted saves
- Change the picture of encrypted saves
- Change the titles of encrypted saves
- Quickly resign pre stored saves
- Convert gamesaves from PS4 to PC or vice versa (some games require extra conversion, those implemented are in table below) 
- Add quick cheats to your games (available games are in table below)
- Apply save wizard quick codes to your saves
- Create saves from scratch

## Functionalities
- File uploads through discord and google drive (bulk uploads are supported on all save pair commands)
- File security checks
- Game custom cryptography handling (extra encryption layer based on game, in table below)
- Param.sfo parser
- Asynchronous, can handle multiple operations at once
- Bot will guide you with what do to in each command
- All commands except ping will only work in private threads created by the bot, thread IDs are stored in .db file
- Everything will get cleaned up locally and on the PS4
- All commands that takes save pairs will resign
- Account ID database, do not include playstation_id parameter if you want to use previously stored account ID
- Interactive user interface

| Second layer encryption game list        | PS4 -> PC conversion and vice versa | Quick cheats             | Extra re-region support (more than keystone & title id swapping) |
| ---------------------------------------- | ----------------------------------- | ------------------------ | ---------------------------------------------------------------- |
| Borderlands 3                            | Borderlands 3                       |                          |                                     |
| Dead Island 1 (compression only)         |                                     |                          |                                     |
| Dead Island 2 (compression only)         |                                     |                          |                                     |
| Dying Light 1 (compression only)         |                                     |                          |                                     |
| Dying Light 2 (compression only)         |                                     |                          |                                     |
| Grand Theft Auto V                       | Grand Theft Auto V                  | Grand Theft Auto V       |                                     |
| Like a Dragon: Ishin                     |                                     |                          |                                     |
| Metal Gear Solid V: Ground Zeroes        |                                     |                          | Metal Gear Solid V: Ground Zeroes   |
| Metal Gear Solid V: The Phantom Pain     |                                     |                          | Metal Gear Solid V: The Phantom Pain|
| No Man's Sky (savedata.hg)               |                                     |                          |                                     |
| Raspberry Cube                           |                                     |                          |                                     |
| Red Dead Redemption 2                    | Red Dead Redemption 2               | Red Dead Redemption 2    |                                     |
| Resident Evil Revelations 2              |                                     |                          |                                     |
| Shin Megami Tensei 5                     |                                     |                          |                                     |
| Terraria (.plr & some .wld)              |                                     |                          |                                     |
| The Last of Us                           |                                     |                          |                                     |
| The Last of Us Part II                   |                                     |                          |                                     |
| Tiny Tina's Wonderlands                  | Tiny Tina's Wonderlands             |                          |                                     |
| Uncharted 4                              |                                     |                          |                                     |
| Uncharted: The Lost Legacy               |                                     |                          |                                     |
| Uncharted: The Nathan Drake Collection   |                                     |                          |                                     |
| Xenoverse 2                              |                                     |                          | Xenoverse 2                         |

If you wanna contribute to this list, please let me know!

### Disclaimers
- Bot is down for a couple minutes at a time, usually for maintence
- Saves created using this application will work on SaveWizard

## Credits
- https://github.com/Team-Alua/cecie.nim for creating the homebrew app that makes this possible, in addition to helping me
- https://github.com/dylanbbk & https://github.com/iCrazeiOS for help
- https://github.com/bucanero/save-decrypters for the extra encryption methods
- https://github.com/bucanero/pfd_sfo_tools/blob/master/sfopatcher/src/sfo.c for the param.sfo parser
- https://github.com/bucanero/apollo-lib/blob/main/source/patches.c#L2781 for the quick codes implementation
- https://github.com/Zhaxxy/rdr2_enc_dec/blob/main/rdr2_enc_dec.py for the checksum
- https://github.com/Zhaxxy/xenoverse2_ps4_decrypt for Xenoverse 2 extra layer of encryption
- https://github.com/monkeyman192/MBINCompiler/releases/tag/v5.02.0-pre2 for No Man's Sky obfuscation (mapping.json)
- https://github.com/hzhreal/HTOS for the original project and continued forking of it
