import smartpy as sp

class DiceRollingGame(sp.Contract):
    def __init__(self):
        self.init(
            players = sp.map(tkey=sp.TAddress, tvalue=sp.TNat),
            total_bet = sp.mutez(0),
            is_game_open = True
        )
    
    @sp.entry_point
    def guess(self, guess):
        sp.verify(self.data.is_game_open, message="The game is not open for guesses.")
        sp.verify(guess >= 1 and guess <= 6, message="Guess must be in the range [1, 6].")
        sp.verify(sp.sender not in self.data.players, message="You have already made a guess.")
        
        self.data.players[sp.sender] = guess
        self.data.total_bet += sp.amount
    
    @sp.entry_point
    def distribute_winnings(self, winning_number):
        sp.verify(not self.data.is_game_open, message="The game is still open for guesses.")
        sp.verify(sp.sender == sp.administrator, message="Only the administrator can distribute winnings.")
        
        total_winners = 0
        for player, guess in self.data.players.items():
            if guess == winning_number:
                total_winners += 1
        
        if total_winners > 0:
            individual_share = self.data.total_bet / total_winners
            for player, guess in self.data.players.items():
                if guess == winning_number:
                    sp.transfer(individual_share, sp.tez(0), player)
        
        self.init(is_game_open=True)  # Reset the game for the next round

@sp.add_test(name="Test Dice Rolling Game")
def test_dice_rolling_game():
    scenario = sp.test_scenario()
    
    # Initialize the contract
    contract = DiceRollingGame()
    scenario += contract
    
    # Alice and Bob join the game and place their bets
    scenario += contract.guess(guess=3).run(sender=sp.address("tz1Alice"), amount=sp.tez(1))
    scenario += contract.guess(guess=4).run(sender=sp.address("tz1Bob"), amount=sp.tez(1))
    
    # The game is still open for more guesses
    scenario += contract.guess(guess=5).run(sender=sp.address("tz1Eve"), amount=sp.tez(1))
    
    # Alice closes the game and distributes winnings for guess 3
    scenario += contract.distribute_winnings(winning_number=3).run(sender=sp.address("tz1Alice"))
    
    # Attempt to distribute winnings again (should fail as the game is open)
    scenario += contract.distribute_winnings(winning_number=3).run(sender=sp.address("tz1Alice")).assert_fail()
