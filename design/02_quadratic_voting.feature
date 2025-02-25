Feature: Quadratic Voting
  As a DAO member
  I want to participate in quadratic voting
  So that voting power is distributed more equitably

  Background:
    Given I am a verified DAO member
    And I have governance tokens
    And there is an active proposal in "VOTING" status

  Scenario: Calculate voting cost using quadratic function
    Given I have 100 voting credits
    When I check the cost for different vote counts
    Then I should see the following costs:
      | Vote Count | Credit Cost |
      | 1          | 1           |
      | 2          | 4           |
      | 3          | 9           |
      | 5          | 25          |
      | 10         | 100         |

  Scenario: Vote with maximum allowed voting power
    Given the total voting power for the proposal is 10000 credits
    And the maximum voting power percentage is 25%
    When I try to cast 51 votes on the proposal
    Then I should receive an error message
    And my vote should not be recorded
    And my voting credits should not be deducted

  Scenario: Split voting power between multiple proposals
    Given there are two active proposals in "VOTING" status
    And I have 100 voting credits
    When I cast 5 votes in favor of the first proposal
    And I cast 7 votes against the second proposal
    Then 25 credits should be deducted for the first proposal
    And 49 credits should be deducted for the second proposal
    And I should have 26 voting credits remaining

  Scenario: Delegate voting power to another member
    Given I have 100 voting credits
    And there is another member "delegate_user"
    When I delegate my voting power to "delegate_user"
    Then "delegate_user" should have my voting credits added to their balance
    And I should not be able to vote directly
    And "delegate_user" can vote with my delegated credits

  Scenario: Undelegate voting power
    Given I have delegated my 100 voting credits to "delegate_user"
    When I undelegate my voting power
    Then my 100 voting credits should be returned to me
    And "delegate_user" should no longer have my delegated credits
    And I should be able to vote directly again

  Scenario: Vote with delegated voting power
    Given I have 50 voting credits
    And "delegator_user" has delegated 100 voting credits to me
    When I cast 10 votes in favor of a proposal
    Then 100 credits should be deducted from my total voting power
    And the proposal should record 10 votes in favor from me
    And both my and "delegator_user" governance tokens should be locked for 30 days 