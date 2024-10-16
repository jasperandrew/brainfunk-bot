import json
import os
import re

import discord
import requests
from replit import db

# CHANGE THIS VARIABLE TO YOUR REPLIT USERNAME #
USER = 'quazillionaire'

# GLOBALS #
CLIENT = discord.Client()
API_URL = 'https://BrainfuckAPI.{0}.repl.co'.format(USER)

DELIM_KEY = 'delim'
CELLSIZE_KEY = 'cellsize'
RAWINPUT_KEY = 'rawinput'

SETTINGS = {
    DELIM_KEY: {
        'DEFAULT': '|'
    },
    CELLSIZE_KEY: {
        'DEFAULT': '8',
        'VALID': ['8', 'U8', '16', 'U16', '32', 'U32', '64', 'U64']
    },
    RAWINPUT_KEY: {
        'DEFAULT': 'false',
        'VALID': ['true', 'false']
    }
}

# INITIALIZE #############################################################


def initialize():
  print('Initializing Brainfunk...\n\tChecking for BrainfuckAPI...', end='')

  response = requests.get('{0}/status'.format(API_URL))
  if response.text != 'ONLINE':
    print(
        '[FAIL]\nInitialization FAIL\nBrainfuckAPI required. See README.md for details.\nExiting...'
    )
    return

  print('[OK]\n\tChecking for access token...', end='')

  if 'token' not in os.environ:
    print(
        '[FAIL]\nInitialization FAIL\nDiscord access token required. See README.md for details.\nExiting...'
    )
    return

  print('[OK]\n\tStarting Discord client.....', end='')

  try:
    CLIENT.run(os.environ['token'])
  except:
    print(
        '[FAIL]\nInitialization FAIL\nInvalid Discord access token. Make sure you copied it exactly. See README.md for setup instructions.\nExiting...'
    )
    return


# DISCORD FUNCTIONS #############################################################


# Called when the bot is logged in
@CLIENT.event
async def on_ready():
  print('[OK]\nInitialization OK\nLogged in as {0}'.format(CLIENT.user))


# Called when a message is received
@CLIENT.event
async def on_message(msg):
  if msg.author == CLIENT.user:
    return

  print(msg.author.id)

  if msg.content.split(' ')[0].lower() in ['/bf', '/bfi']:
    s = msg.content.lstrip('/bf ')  # string
    await process(s, msg)


# Output a message to a discord channel
async def send_msg(c, s):
  await c.send(s)


# Sends a decorated error message to a discord channel
async def send_err(c, s):
  await send_msg(c, ':no_entry_sign: {0}'.format(s))


# PRIMARY FUNCTIONS #############################################################


# Process a command
async def process(s, m):
  c = m.channel
  s = s.split(' ', 1)
  cmd, s = s[0].lower(), s[1] if len(s) > 1 else ''
  if cmd in ['interpret', 'i']:
    await interpret(s, m)
  elif cmd == 'config':
    await configure(s, m)
  elif cmd in ['help', 'about']:
    await about(s, m)
  else:
    await send_err(
        c,
        'Invalid command: `{0}`. Use `/bf help commands` for details.'.format(
            cmd))


# Interpret some code
async def interpret(s, m):
  c, g = m.channel, str(m.guild.id)
  delim = db_get(g, DELIM_KEY)
  signed, bits = parse_cell_size(db_get(g, CELLSIZE_KEY))
  code, inputs = extract_input(s, delim)
  code = minify_code(code)

  if code == '':
    await send_err(
        c, 'There\'s nothing to run! Try `/bf help` if you\'re stuck.')
    return

  if inputs != '' and db_get(g, RAWINPUT_KEY) == 'true':
    try:
      inputs = list(map(int, inputs.split(',')))
    except:
      await send_err(
          c,
          'Malformed input. Check that `rawinput` is set correctly. See `/bf help config` for details.'
      )
      return

  response = requests.post('{0}/interpret'.format(API_URL),
                           json={
                               'code': code,
                               'input': inputs,
                               'bits': bits,
                               'signed': signed
                           })

  await send_msg(c, build_output(json.loads(response.text)))


# Read or change settings
async def configure(s, m):
  c, g = m.channel, str(m.guild.id)
  if s == '':
    out_str = ':gear: Current settings'
    for k in SETTINGS.keys():
      v = db_get(g, k)
      if v == '`':
        v = '` '
      out_str += '\n`{0}` → `{1}`'.format(k, v)
    await send_msg(c, out_str)
    return

  s = s.split(' ', 1)
  if s[0].lower() == 'set':
    mode = 'set'
  elif s[0] == 'reset':
    mode = 'reset'
  else:
    await send_err(
        c, 'Invalid config command: `{0}`. Use `/bf help config` for details.'.
        format(s[0]))
    return

  if len(s) < 2:
    await send_err(c, 'Missing parameters. Use `/bf help config` for details.')
    return

  s = s[1].split(' ', 1)
  if mode == 'set' and len(s) < 2:
    await send_err(c, 'Missing parameters. Use `/bf help config` for details.')
    return

  key = s[0]
  if mode == "reset" and key == 'all':
    for k in SETTINGS.keys():
      db_set(g, k, SETTINGS[k]['DEFAULT'])
    await send_msg(
        c, ':gear: Successfully reset all settings to default values.')
    return

  if key not in SETTINGS.keys():
    await send_err(
        c,
        'No setting called `{0}` exists. Use `/bf help config` for details.'.
        format(key))
    return

  val = s[1] if mode == 'set' else SETTINGS[key]['DEFAULT']
  if not setting_is_valid(key, val):
    await send_err(
        c,
        '`{0}` is not a valid value for `{1}`. Use `/bf help config` for details.'
        .format(val, key))
    return

  db_set(g, key, val)
  if val == '`':
    val = '` '
  await send_msg(
      c, ':gear: Successfully {0} `{1}` to `{2}`.'.format(mode, key, val))


# Send help messages
async def about(s, m):
  c, g = m.channel, str(m.guild.id)
  s = s.split(' ', 1)
  if s[0] == 'commands':
    await send_msg(c, COMMAND_STR)
  elif s[0] == 'examples':
    await send_msg(c, EXAMPLE_STR.format(db_get(g, DELIM_KEY)))
  elif s[0] == 'settings' or s[0] == 'config':
    await send_msg(
        c,
        SETTINGS_STR.format('Any whitespace-free string',
                            SETTINGS[DELIM_KEY]['DEFAULT'],
                            list_to_str(SETTINGS[CELLSIZE_KEY]['VALID']),
                            SETTINGS[CELLSIZE_KEY]['DEFAULT'],
                            list_to_str(SETTINGS[RAWINPUT_KEY]['VALID']),
                            SETTINGS[RAWINPUT_KEY]['DEFAULT']))
  else:
    await send_msg(c, ABOUT_STR)


# HELPER FUNCTIONS #############################################################


# Remove any non-Brainfuck characters
def minify_code(code):
  return ''.join(
      [x for x in list(code) if x in ['+', '-', '<', '>', '[', ']', ',', '.']])


# Pull out input from the command string
def extract_input(s, delim):
  if delim not in s:
    return (s, '')

  s = s.split(delim, 1)
  return (s[0], s[1])


# Parse a cell size string into bool/int values
def parse_cell_size(cellsize):
  if cellsize.startswith('U'):
    signed = False
  else:
    signed = True

  cellsize = cellsize.lstrip('U')

  return (signed, int(cellsize))


# Build the output string for a interpret result
def build_output(result_json):
  status = result_json['status']
  out_str = ''
  if status == 'complete':
    out_str += ':white_check_mark: Ran to completion'
  elif status == 'waiting':
    out_str += ':warning: Stopped (reached end of input)'
  elif status == 'stopped':
    out_str += ':fire: Parse error (missing a loop bracket?)'
  else:
    out_str += ':interrobang: Uh oh, something is messed up...'

  raw_output = result_json['output']
  if raw_output != []:
    out_str += '\nOutput (raw): `{0}`\nOutput (text): `{1}`'.format(
        ','.join(map(str, raw_output)), ''.join(map(chr, raw_output)))

  return out_str


# Get a value from the database
def db_get(g, k):
  if g in db and k in db[g]:
    return db[g][k]
  return SETTINGS[k]['DEFAULT']


# Put a value in the database
def db_set(g, k, v):
  if g in db:
    config = db[g]
    config[k] = v
    db[g] = config
  else:
    config = {k: v}
    db[g] = config


# Checks if a setting is valid
def setting_is_valid(k, v):
  if k == DELIM_KEY:
    if v == '' or re.sub(r"\s", '', v) != v:
      return False

  if k == CELLSIZE_KEY:
    if v not in SETTINGS[k]['VALID']:
      return False

  if k == RAWINPUT_KEY:
    if v not in SETTINGS[k]['VALID']:
      return False

  return True


# Convert string list to string
def list_to_str(l):
  out = l[0]
  for s in l[1:]:
    out += ',' + s
  return out


# ABOUT STRINGS #############################################################

ABOUT_STR = ''':brain::point_right::ok_hand: ` + - < > [ ] . , `
Brainfuck is an esoteric programming language with only 8 symbols!
https://wikipedia.org/wiki/Brainfuck
~~                                    ~~
Use `/bf help commands` for details on the available commands
Try `/bf help examples` to see a few example programs you can run yourself
'''.strip()

COMMAND_STR = ''':blue_book: Reference (Commands)
☙ `interpret <code>`: Interpret some Brainfuck code
      ‣ `interpret <code>|<input>`: Supply input to the program
☙ `config`: View bot settings
      ‣ `config set <name> <value>`: Change a setting
      ‣ `config reset <name>`: Reset a setting to its default
      ‣ `config reset all`: Reset all settings to default
☙ `help`: Display the about message.
      ‣ `help settings`: Details on the settings
      ‣ `help commands`: This message
      ‣ `help examples`: Example programs
'''.strip()

EXAMPLE_STR = ''':blue_book: Reference (Examples)
Hello World:```/bfi ++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.```
ROT13 Cipher:```/bfi -,+[-[>>++++[>++++++++<-]<+<-[>+>+>-[>>>]<[[>+<-]>>+>]<<<<<-]]>>>[-]+>--[-[<->+++[-]]]<[++++++++++++<[>-[>+>>]>[+[<+>-]>+>>]<<<<<-]>>[<+>-]>[-[-<<[-]>>]<<[<<->>-]>>]<<[<<+>>-]]<[-]<.[-]<-,+]{0}Cipher? I hardly know 'er!```
'''.strip()

SETTINGS_STR = ''':blue_book: Reference (Settings)
☙ `delim`: Set the delimiter for grouping program input.
      ‣ Valid values: `{0}` (default: `{1}`)
☙ `cellsize`: Set the size, in bits, of the virtual cells used by the Brainfuck interpreter. Note: `U` designates an unsigned integer.
      ‣ Valid values: `{2}` (default: `{3}`)
☙ `rawinput`: If true, input will be read as a comma-separated integer list.
      ‣ Valid values: `{4}` (default: `{5}`)
'''.strip()

# MAIN #############################################################


def main():
  initialize()


main()
