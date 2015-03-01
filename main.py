#!/usr/bin/env python3
import os, sys, pickle, random, string, time

class Player:
	def __init__(self):
		# a player's hand
		self.hand = []
		# a player's discard pile
		self.discard = []
		# whether the player is in the game
		self.alive = True
		# wins
		self.score = 0
	def start(self, card):
		self.hand.clear()
		self.discard.clear()
		self.hand.append(card)
		self.alive = True
	# put the player out of game
	def kill(self):
		self.alive = False
		self.discard.extend(self.hand)
		self.hand.clear()

class LoveLetter:
	def __init__(self, nplayers):
		self.nplayers = nplayers
		self.last_first = random.randrange(0, nplayers)
		self.players = dict((i, Player()) for i in range(nplayers))
		self.new_round()
	def new_round(self):
		# setup deck
		self.deck_init()
		# initialise
		self.setup()
		# create players
		self.player_setup()
	def deck_init(self):
		# create deck
		self.deck = 1 * ['Princess'] + 1 * ['Minister'] + 1 * ['General'] + 2 * ['Wizard'] + 2 * ['Priestess'] + 2 * ['Knight'] + 2 * ['Clown'] + 5 * ['Soldier']
		# shuffle deck
		random.shuffle(self.deck)
		# discard 1 card
		self.deck.pop()
	def setup(self):
		# turn and phase init
		self.turn = (self.last_first + 1) % self.nplayers
		self.last_first = self.turn
		self.phase = 0
	def player_setup(self):
		# player hand and notification setup
		for i in self.players:
			self.players[i].start(self.deck.pop())
		self.notify = self.nplayers * ['']
	# the main function
	def next(self, player, choice = '', arg = ''):
		# whether the page should auto-refresh
		refresh = 'true'
		# main message
		msg = ''
		if player == -1: # this person is not a player
			msg = 'You are an observer'
		elif self.notify[player] != '':
			msg, self.notify[player] = self.notify[player], ''
		elif player != self.turn: # it is not this player's turn
			if self.phase == 0: 
				msg = 'Another player is drawing'
			elif self.phase == 1: 
				msg = 'Another player has drawn'
			elif self.phase == 2: 
				msg = 'Another player is discarding'
			elif self.phase == 3: 
				msg = 'Another player has discarded'
			elif self.phase == 4: 
				msg = 'Another player has ended their turn'
			elif self.phase == 10: 
				msg = 'Round over'
		else: # it is the player's turn
			cur = self.players[self.turn]
			if self.phase == 0: # draw
				card = self.deck.pop()
				cur.hand.append(card)
				msg = 'You drew ' + card
			elif self.phase == 1: # post-draw
				if 'Minister' in cur.hand and self.hvalue(self.turn) >= 12:
					self.players[self.turn].kill()
					msg = 'Minister has killed you'
				msg = 'No post-draw effect'
			elif self.phase == 2: # discard
				if choice == '': # still deciding
					refresh = 'false'
					msg = 'Choose card to discard:'
					for c in cur.hand:
						msg += '<input type="submit" name="choice" value="' + c + '"/>'
					self.phase -= 1
				else: # decided
					cur.hand.remove(choice)
					cur.discard.append(choice)
					msg = 'You discarded ' + choice
			elif self.phase == 3: # discard effect
				played = cur.discard[-1]
				if played == 'Princess': # suicide discard
					self.players[self.turn].kill()
					msg = 'You discarded the Princess :('
				elif played == 'Minister' or played == 'Priestess': # boring discards
					msg = 'No effect'
				elif choice == '' or self.players[int(choice)].alive == False: # deciding target
					refresh = 'false'
					msg = 'Choose ' + played + ' target:'
					for i in self.players:
						if self.players[i].alive and (i != self.turn or played == 'Wizard'):
							msg += '<input type="submit" name="choice" value="' + str(i) + '"/>'
					self.phase -= 1
				else: # decided target
					choice = int(choice)
					target = self.players[choice]
					self.broadcast(self.turn, choice, played)
					if len(target.discard) == 0 or target.discard[-1] != 'Priestess': # only execute if target's last discard was not a Priestess
						if played == 'General':
							cur.hand, target.hand = target.hand, cur.hand
							msg = 'Swapped hands with Player ' + str(choice)
							self.notify[choice] = 'Swapped hands with Player ' + str(self.turn)
						elif played == 'Wizard':
							target.discard.extend(target.hand)
							target.hand = [self.deck.pop()]
							msg = 'Player ' + str(choice) + ' discarded their hand'
							if choice != self.turn:
								self.notify[choice] = 'Your hand was discarded by Player ' + str(self.turn)
						elif played == 'Knight':
							if self.hvalue(self.turn) > self.hvalue(choice):
								msg = 'Your ' + str(cur.hand) + ' beats their ' + str(target.hand)
								self.notify[choice] = 'Knighted by Player ' + str(self.turn) + ': Their ' + str(cur.hand) + ' beats your ' + str(target.hand)
								self.players[choice].kill()
							elif self.hvalue(self.turn) < self.hvalue(choice):
								msg = 'Your ' + str(cur.hand) + ' loses to their ' + str(target.hand)
								self.notify[choice] = 'Knighted by Player ' + str(self.turn) + ': Their ' + str(cur.hand) + ' loses to your ' + str(target.hand)
								self.players[self.turn].kill()
							else:
								msg = 'Your ' + str(cur.hand) + ' equals their ' + str(target.hand)
								self.notify[choice] = 'Knighted by Player ' + str(self.turn) + ': Their ' + str(cur.hand) + ' equals your ' + str(target.hand)
						elif played == 'Clown':
							msg = 'Their hand was: ' + str(target.hand)
							self.notify[choice] = 'Player ' + str(self.turn) + ' looked at your hand'
						elif played == 'Soldier':
							if arg == '' or arg == 'Soldier':
								refresh = 'false'
								msg = 'Name card:'
								msg += '<input type="hidden" name="choice" value="' + str(choice) + '"/>'
								deck = list(self.deck)
								for i in self.players:
									if i != self.turn:
										deck.extend(self.players[i].hand)
								deck = list(set(deck))
								for c in deck:
									if c != 'Soldier':
										msg += '<input type="submit" name="arg" value="' + c + '">'
								self.phase -= 1
							elif target.hand[0] == arg:
								self.players[choice].kill()
								msg = 'You were correct'
								self.notify[choice] = 'Player ' + str(self.turn) + ' named your hand correctly'
							else:
								msg = 'You were incorrect'
								self.notify[choice] = 'Player ' + str(self.turn) + ' guessed your hand to be ' + arg
					else:
						msg = 'Effect ignored'
			elif self.phase == 4: # end turn
				self.change()
				self.phase = -1
				msg = 'End turn'
			elif self.phase == 10: # round over
				msg = 'You win the round'
				self.players[self.turn].score += 1
				self.new_round()
				self.phase -= 1
			self.phase += 1
			if self.nalive() == 1: # move to game over if only one player left
				self.change()
				self.phase = 10
		stats = ''
		for i in self.players:
			stats += 'Player ' + str(i) + ' (score=' + str(self.players[i].score) + ')' + ' Alive: ' + str(self.players[i].alive) + '<br/>'
			#stats += 'Current hand: ' + str(self.players[i].hand) + '<br/>'
			stats += 'Discards: ' + str(self.players[i].discard) + '<br/>'
		stats += '<br/>Your hand: ' + str(self.players[player].hand) + '<br/>'
		resp = {'msg': stats + '<strong>' + msg + '</strong>', 'refresh': refresh}
		return resp
	# notify players about a public event
	def broadcast(self, s, t, evt):
		for i in self.players:
			if i != s and i != t:
				self.notify[i] = 'Player ' + str(s) + ' ' + evt + 'ing Player ' + str(t)
	# count the number of players in game
	def nalive(self):
		alive = 0
		for i in self.players:
			if self.players[i].alive:
				alive += 1
		return alive
	# calculate the value of a players hand
	def hvalue(self, who):
		cvalue = {'Princess': 8, 'Minister': 7, 'General': 6, 'Wizard': 5, 'Priestess': 4, 'Knight': 3, 'Clown': 2, 'Soldier': 1}
		v = 0
		for c in self.players[who].hand:
			v += cvalue[c]
		return v
	# rotate to next player still in game
	def change(self):
		self.turn = (self.turn + 1) % self.nplayers
		while self.players[self.turn].alive == False:
			self.turn = (self.turn + 1) % self.nplayers

# the entry point
def application(env, start_response):
	# send ack
	start_response('200 OK', [('Content-Type','text/html')])
	# extract the GET arguments
	get = env['QUERY_STRING'].split('&')
	# parse the GET arguments
	if len(get) > 0: # there are arguments to parse
		query = dict(qc.split('=') for qc in get)
		query['player'] = int(query.get('player', -1)) # cast 'player' into a int, defaulting to -1
	else: # there are no arguments to parse
		query = {'player': -1} # default 'player' to -1
	# get a game id
	gid = query.get('id')
	if gid != None:
		gid = query['id']
		del query['id']
	else:
		gid = hex(int(time.time()))[2:]
	# create or load game
	if query.get('new') != None: # if there's a 'new' argument, create a new game with 'new' players
		game = LoveLetter(int(query['new']))
		del query['new']
	else: # load an existing game, or create a new game with 2 players if none exists
		try:
			with open('data/game-' + gid + '.pickle', 'rb') as f:
				game = pickle.load(f)
		except:
			game = LoveLetter(2)
	# pass arguments to game
	resp = game.next(**query)
	# save game state
	with open('data/game-' + gid + '.pickle', 'wb') as f:
		pickle.dump(game, f)
	# generate HTML
	html = string.Template('''
	<!DOCTYPE html>
	<html>
	<head>
		<meta charset="UTF-8"/>
		<title>Love Letter</title>
		</head>
	<body onload="window.setTimeout(function() { if ($refresh) { window.location.replace(location.pathname + '?id=$id&player=$player'); } }, 3000);"><form><input type="hidden" name="id" value="$id"/><input type="hidden" name="player" value="$player"/>
		$resp
	</form></body>
	</html>
	''').safe_substitute(id = gid, player = query['player'], resp = resp['msg'], refresh = resp['refresh'])
	return [bytes(html, 'utf-8')]
