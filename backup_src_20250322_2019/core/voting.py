"""
Voting system for the hub-and-spoke architecture.

This module implements a voting system for critical decisions,
allowing multiple crews to vote on the best approach.
"""

import logging
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum

logger = logging.getLogger(__name__)


class VoteWeight(Enum):
    """Weights for different voter types."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 5


class VotingSystem:
    """System for crews to vote on critical decisions."""
    
    def __init__(self, threshold: float = 0.6, min_voters: int = 2):
        """
        Initialize the voting system.
        
        Args:
            threshold: Threshold for decision (fraction of total weight)
            min_voters: Minimum number of voters required
        """
        self.threshold = threshold
        self.min_voters = min_voters
    
    def conduct_vote(self, 
                     question: str,
                     options: List[str],
                     voters: Dict[str, Dict[str, Any]],
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Conduct a vote among crews.
        
        Args:
            question: The question to vote on
            options: List of options to vote for
            voters: Dictionary of voter IDs to voter info
            context: Additional context for the vote
            
        Returns:
            Result of the vote
        """
        if len(voters) < self.min_voters:
            return {
                "status": "failed",
                "reason": f"Not enough voters. Need at least {self.min_voters}.",
                "winner": None,
                "votes": {}
            }
        
        # Collect votes
        votes = {}
        total_weight = 0
        
        for voter_id, voter_info in voters.items():
            # Get the voter's weight
            weight = self._get_voter_weight(voter_info)
            total_weight += weight
            
            # Get the voter's vote
            vote = self._get_vote(voter_id, voter_info, question, options, context)
            
            if vote in options:
                votes[voter_id] = {
                    "option": vote,
                    "weight": weight,
                    "reason": voter_info.get("reason", "")
                }
            else:
                logger.warning(f"Invalid vote from {voter_id}: {vote}")
        
        # Count weighted votes
        option_scores = {option: 0 for option in options}
        
        for voter_id, vote_info in votes.items():
            option = vote_info["option"]
            weight = vote_info["weight"]
            option_scores[option] += weight
        
        # Determine winner
        winner = max(option_scores.items(), key=lambda x: x[1])
        winner_option, winner_score = winner
        
        # Check if winner meets threshold
        if winner_score / total_weight >= self.threshold:
            status = "success"
        else:
            status = "no_consensus"
        
        return {
            "status": status,
            "winner": winner_option,
            "winner_score": winner_score,
            "total_weight": total_weight,
            "threshold": self.threshold,
            "votes": votes,
            "option_scores": option_scores
        }
    
    def _get_voter_weight(self, voter_info: Dict[str, Any]) -> int:
        """
        Get the weight of a voter.
        
        Args:
            voter_info: Information about the voter
            
        Returns:
            Weight of the voter
        """
        weight_str = voter_info.get("weight", "NORMAL")
        
        if isinstance(weight_str, str):
            try:
                return VoteWeight[weight_str].value
            except KeyError:
                return VoteWeight.NORMAL.value
        
        return weight_str if isinstance(weight_str, int) else VoteWeight.NORMAL.value
    
    def _get_vote(self, voter_id: str, voter_info: Dict[str, Any],
                 question: str, options: List[str],
                 context: Optional[Dict[str, Any]] = None) -> str:
        """
        Get a vote from a voter.
        
        Args:
            voter_id: ID of the voter
            voter_info: Information about the voter
            question: The question to vote on
            options: List of options to vote for
            context: Additional context for the vote
            
        Returns:
            The voter's choice
        """
        # If the voter has a vote_function, call it
        vote_function = voter_info.get("vote_function")
        
        if vote_function and callable(vote_function):
            try:
                return vote_function(question, options, context)
            except Exception as e:
                logger.error(f"Error getting vote from {voter_id}: {e}")
                return options[0] if options else ""
        
        # If the voter has a predefined vote, use it
        predefined_vote = voter_info.get("vote")
        
        if predefined_vote in options:
            return predefined_vote
        
        # Default to first option
        return options[0] if options else ""


class ConflictResolver:
    """System for resolving conflicts between crews."""
    
    def __init__(self, voting_system: Optional[VotingSystem] = None):
        """
        Initialize the conflict resolver.
        
        Args:
            voting_system: Voting system to use
        """
        self.voting_system = voting_system or VotingSystem()
    
    def resolve_conflict(self, 
                         conflict: Dict[str, Any],
                         crews: Dict[str, Any],
                         context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Resolve a conflict between crews.
        
        Args:
            conflict: Description of the conflict
            crews: Dictionary of crew IDs to crew objects
            context: Additional context for resolution
            
        Returns:
            Resolution of the conflict
        """
        # Extract conflict details
        conflict_type = conflict.get("type", "general")
        conflict_description = conflict.get("description", "")
        options = conflict.get("options", [])
        
        # Prepare voters
        voters = {}
        
        for crew_id, crew in crews.items():
            # Skip crews that aren't relevant to this conflict
            if not self._is_crew_relevant(crew, conflict_type, context):
                continue
            
            # Add crew as voter
            voters[crew_id] = {
                "weight": self._get_crew_weight(crew, conflict_type),
                "vote_function": lambda q, o, c: self._get_crew_vote(crew, q, o, c)
            }
        
        # Conduct vote
        result = self.voting_system.conduct_vote(
            question=conflict_description,
            options=options,
            voters=voters,
            context=context
        )
        
        # If no consensus, use fallback resolution
        if result["status"] != "success":
            result["fallback"] = self._fallback_resolution(conflict, context)
        
        return result
    
    def _is_crew_relevant(self, crew: Any, conflict_type: str,
                         context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if a crew is relevant to a conflict.
        
        Args:
            crew: The crew to check
            conflict_type: Type of conflict
            context: Additional context
            
        Returns:
            True if the crew is relevant, False otherwise
        """
        # This is a placeholder - in the actual implementation, we would
        # check if the crew is relevant based on its type and the conflict type
        return True
    
    def _get_crew_weight(self, crew: Any, conflict_type: str) -> Union[int, str]:
        """
        Get the weight of a crew for a conflict type.
        
        Args:
            crew: The crew
            conflict_type: Type of conflict
            
        Returns:
            Weight of the crew
        """
        # This is a placeholder - in the actual implementation, we would
        # determine the weight based on the crew's expertise in the conflict area
        
        # Example: Sales crew has higher weight for pricing conflicts
        if hasattr(crew, "function_type") and conflict_type == "pricing":
            if crew.function_type == "sales":
                return VoteWeight.HIGH.value
        
        return VoteWeight.NORMAL.value
    
    def _get_crew_vote(self, crew: Any, question: str, 
                      options: List[str], 
                      context: Optional[Dict[str, Any]] = None) -> str:
        """
        Get a vote from a crew.
        
        Args:
            crew: The crew
            question: The question to vote on
            options: List of options to vote for
            context: Additional context
            
        Returns:
            The crew's choice
        """
        # This is a placeholder - in the actual implementation, we would
        # call a method on the crew to get its vote
        
        # If the crew has a vote method, call it
        if hasattr(crew, "vote") and callable(crew.vote):
            try:
                return crew.vote(question, options, context)
            except Exception as e:
                logger.error(f"Error getting vote from crew: {e}")
        
        # Default to first option
        return options[0] if options else ""
    
    def _fallback_resolution(self, conflict: Dict[str, Any],
                            context: Optional[Dict[str, Any]] = None) -> str:
        """
        Provide a fallback resolution when voting fails.
        
        Args:
            conflict: Description of the conflict
            context: Additional context
            
        Returns:
            Fallback resolution
        """
        # This is a placeholder - in the actual implementation, we would
        # have more sophisticated fallback strategies
        
        # Default to the first option
        options = conflict.get("options", [])
        if options:
            return options[0]
        
        return "No resolution available"


class DecisionMaker:
    """System for making critical decisions using the voting system."""
    
    def __init__(self, voting_system: Optional[VotingSystem] = None):
        """
        Initialize the decision maker.
        
        Args:
            voting_system: Voting system to use
        """
        self.voting_system = voting_system or VotingSystem()
    
    def make_decision(self, 
                     question: str,
                     options: List[str],
                     crews: Dict[str, Any],
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a decision by voting among crews.
        
        Args:
            question: The question to decide on
            options: List of options to choose from
            crews: Dictionary of crew IDs to crew objects
            context: Additional context for the decision
            
        Returns:
            Result of the decision
        """
        # Prepare voters
        voters = {}
        
        for crew_id, crew in crews.items():
            # Add crew as voter
            voters[crew_id] = {
                "weight": self._get_crew_decision_weight(crew, question, context),
                "vote_function": lambda q, o, c: self._get_crew_decision(crew, q, o, c)
            }
        
        # Conduct vote
        result = self.voting_system.conduct_vote(
            question=question,
            options=options,
            voters=voters,
            context=context
        )
        
        return result
    
    def _get_crew_decision_weight(self, crew: Any, question: str,
                                 context: Optional[Dict[str, Any]] = None) -> Union[int, str]:
        """
        Get the weight of a crew for a decision.
        
        Args:
            crew: The crew
            question: The question to decide on
            context: Additional context
            
        Returns:
            Weight of the crew
        """
        # This is a placeholder - in the actual implementation, we would
        # determine the weight based on the crew's expertise in the decision area
        
        # If the crew has a get_decision_weight method, call it
        if hasattr(crew, "get_decision_weight") and callable(crew.get_decision_weight):
            try:
                return crew.get_decision_weight(question, context)
            except Exception as e:
                logger.error(f"Error getting decision weight from crew: {e}")
        
        return VoteWeight.NORMAL.value
    
    def _get_crew_decision(self, crew: Any, question: str,
                          options: List[str],
                          context: Optional[Dict[str, Any]] = None) -> str:
        """
        Get a decision from a crew.
        
        Args:
            crew: The crew
            question: The question to decide on
            options: List of options to choose from
            context: Additional context
            
        Returns:
            The crew's choice
        """
        # This is a placeholder - in the actual implementation, we would
        # call a method on the crew to get its decision
        
        # If the crew has a make_decision method, call it
        if hasattr(crew, "make_decision") and callable(crew.make_decision):
            try:
                return crew.make_decision(question, options, context)
            except Exception as e:
                logger.error(f"Error getting decision from crew: {e}")
        
        # Default to first option
        return options[0] if options else ""
