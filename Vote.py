from copy import deepcopy
from math import ceil, floor

class Vote:
    """A single vote.
    """
    
    def __init__ (self, prefs = []):
        """Creates the vote using the given list of preferences. If no list is
        passed, creates a white vote.
        """
        
        self.prefs = deepcopy (prefs)
        self.weight = 1.0

    def first_choice (self):
        """Returns the name of the first preference.
        """

        if len (self.prefs) == 0:
            return None
        else:
            return self.prefs [0]

    def is_white (self):
        """Returns True if vote is white, False otherwise.
        """

        if len(self.prefs) == 0:
            return True
        else:
            return False

    def clear (self):
        """Makes the vote white.
        """
        
        self.prefs = []

    def update (self, wcoef=1.0):
        """Updates the vote for moving. Removes first preference and
        multiplies weight by wcoef.
        """

        self.weight *= wcoef
        #Removing the first preference serves the purpose of knowing
        #where to move the vote next
        self.prefs.pop(0)

    def __str__ (self):
        ret = ""
        for pref in self.prefs:
            ret += pref+"\n"
        return ret+"weight = "+str(self.weight)


class Participant:
    """A single participant. Every participant holds a list of votes
    assigned to him.
    """
    
    def __init__ (self, name):
        self.name = deepcopy (name)
        self.votes = []

    def count_votes (self):
        """Return the number of votes currently assigned to the participant object.
        """
        
        ret = 0
        for vote in self.votes:
            ret += vote.weight
        return ret

    def add_vote (self, vote):
        """Assigns given vote to participant.
        """
        
        self.votes.append(vote) #This does not actually copy the vote object

    def destroy_white_votes (self):
        """Destroys white votes assigned to the participant.
        """

        self.votes = [vote for vote in self.votes if not vote.is_white()]

    def clear (self):
        """Empties the list of votes. This is useful when moving votes to next
        preference in order to avoid duplicate pointers.
        """

        self.votes = []

    def __str__ (self):
        ret = "Participant name: " + self.name
        ret += "\nVotes: " + str (self.count_votes())
        return ret

class Context:
    def __init__ (self, participants, seats, votes):

        self.participants = self.get_participants(participants)
        self.seats = seats
        self.votes = self.get_votes(votes)
        self.winners = []
        self.eliminated = []
        self.phase = 0
        self.destroy_white_votes()
        self.quota = 1.0 + (len(self.votes)/(self.seats+1.0))
        self.quota = ceil(self.quota)

    def destroy_white_votes (self):
        """Remove all white votes from the context.
        """
        
        self.votes = [vote for vote in self.votes if not vote.is_white()]

    def complete (self):
        """Returns True if election is over or False if it isn't.
        """
        
        if len(self.winners) == self.seats:
            return True
        else:
            return False

    def find_participant (self, name):
        """Return candidate which matches passed name.
        """

        for participant in self.participants:
            if participant.name == name:
                return participant
        return None

    def migrate (self, source, wcoef):
        """Migrate votes from source to next preference of each vote.
        """

        for vote in source.votes:
            vote.update (wcoef)
            
            # Cycle throught vote's preferences until valid participant is found
            # or vote has become white
            while not vote.is_white():
                first_choice = self.find_participant (vote.first_choice())

                # None means the participant has won or has been eliminated
                if first_choice is not None:
                    first_choice.add_vote(vote)
                    break
                else:
                    vote.update() # Remove the first choice
        source.clear()

    def election_loop (self):
        """Handles the whole election process by repeatedly calling election phase until
        all seats are filled.
        """

        # Initialize by assigning all votes to their first choice
        for vote in self.votes:
            p = self.find_participant(vote.first_choice())
            p.add_vote (vote)

        while not self.complete():
            import ipdb; ipdb.set_trace()
            self.election_phase()

    def election_phase (self):
        """Runs a single election phase.
        """
        # TODO : handle ties by randomly selecting candidate

        self.phase += 1

        #Sorting the participants makes it easier to find the winner/loser
        self.participants.sort(key=lambda p:p.count_votes(), reverse=True)

        first = self.participants [0]

        if first.count_votes() >= self.quota: # There is a winner

            # Move winner from participants to winners
            self.winners.append(first)
            self.participants.pop(0)

            no_of_votes = first.count_votes()
            wcoef = (no_of_votes - self.quota) / no_of_votes
            source = first      # Source of votes to move

        else:                   # Last in ranking must be eliminated
            last = self.participants.pop()
            self.eliminated.append(last)
            wcoef = 1.0
            source = last

            # If after elimination, number of seats left is equal to
            # participants still running, they automatically win
            if len(self.winners) + len (self.participants) == self.seats:
                self.winners = self.winners + self.participants
                self.participants = []

        self.migrate(source, wcoef)

    def get_participants (self, filename):
        """Get list of participant names from given file. Otherwise get user input.
        """

        #filename = raw_input ("Specify file of participant names (leave blank "
        #                      "to input names manually)\n")
        if len(filename) == 0:
            pnames = raw_input("Enter participant names seperated by spaces\n")

        else:
            f = open (filename, "r")
            pnames = f.read()

        #Split string into list and remove duplicates
        pnames = list(set(pnames.split()))
        participants = [Participant(name) for name in pnames]
        return participants

    def get_seats (self):
        seats = int (raw_input ("Specify number of seats to be filled\n"))
        while seats < 1:
            seats = raw_input("Seats must be positive integer\n")
        return seats

    def get_votes (self, filename = None):
        #filename = raw_input ("Specify file of votes (leave blank to input "
        #                      "names manually)\n")

        votes = []
        if len(filename) == 0:
            prefs = raw_input("Input votes seperated by newlines (single empty"
                              "space for white vote)\n")
            while len(prefs) != 0:
                prefs = prefs.split()
                votes.append(Vote(prefs))
                prefs = raw_input()
        else:
            f = open(filename, "r")
            inp = f.read()
            for prefs in inp.split("\n"):
                votes.append(Vote(prefs.split())) # Create list out of every
                                                  # line before creating vote
        return votes

    def __str__ (self):
        """Print list of participant names and number of seats
        """

        ret = ""
        if len(self.winners) > 0:
            ret += "Winners:\n"
            for w in self.winners:
                ret += w.name + "\n"
            ret += "\n"
        if len(self.eliminated) > 0:
            ret += "Eliminated:\n"
            for el in self.eliminated:
                ret += el.name + "\n"
            ret += "\n"
        if len(self.participants) > 0:
            ret += "Still running:\n"
            for p in self.participants:
                ret += p.name + "\n"
        return ret

con = Context ("Participants.txt", 3, "Votes.txt")
con.election_loop()
print con
