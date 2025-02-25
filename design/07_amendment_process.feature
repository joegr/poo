Feature: Amendment Process
  As a DAO member
  I want to be able to propose and vote on amendments to the governance specification
  So that the governance system can evolve and improve over time

  Background:
    Given I am a verified DAO member
    And I have governance tokens

  Scenario: Propose a constitutional amendment
    Given I hold at least 1% of the total governance tokens
    When I submit a constitutional amendment proposal with the following details:
      | Title                      | Description                                | Rationale                           | Implementation Details              |
      | Reduce Voting Period       | Reduce voting period from 7 to 5 days      | Increase governance efficiency      | Update voting period parameter      |
    Then the amendment proposal should be created with status "DRAFT"
    And the proposal should be marked as a constitutional amendment

  Scenario: Extended discussion period for amendments
    Given there is a constitutional amendment proposal with status "DRAFT"
    When I initiate the discussion period
    Then the proposal status should change to "DISCUSSION"
    And a 14-day discussion timer should start
    And all members should be able to comment on the proposal

  Scenario: Extended voting period for amendments
    Given there is a constitutional amendment proposal with status "DISCUSSION"
    And the 14-day discussion period has ended
    When I initiate the voting period
    Then the proposal status should change to "VOTING"
    And a 14-day voting timer should start

  Scenario: Higher approval threshold for amendments
    Given there is a constitutional amendment proposal in "VOTING" status
    And the voting period has ended
    And at least 45% of all possible voting credits were used
    And at least 80% of votes are in favor
    When the voting results are tallied
    Then the proposal status should change to "APPROVED"
    And the proposal should enter a 48-hour timelock period

  Scenario: Amendment fails due to insufficient supermajority
    Given there is a constitutional amendment proposal in "VOTING" status
    And the voting period has ended
    And at least 45% of all possible voting credits were used
    And only 75% of votes are in favor
    When the voting results are tallied
    Then the proposal status should change to "REJECTED"
    And the amendment should not be implemented

  Scenario: Execute an approved amendment
    Given there is a constitutional amendment with status "APPROVED"
    And the 48-hour timelock period has passed
    When the amendment is executed
    Then the amendment status should change to "EXECUTED"
    And the governance specification should be updated
    And all members should be notified of the change
    And the change should be recorded on the blockchain

  Scenario: View amendment history
    When I view the governance specification
    Then I should see the current version of the specification
    And I should be able to view the amendment history
    And for each amendment I should see:
      | Amendment ID | Title                | Execution Date | Proposer      |
      | AMD-001      | Reduce Voting Period | 2023-05-15     | alice.eth     |

  Scenario: Propose multiple amendments simultaneously
    Given there are already 2 active amendment proposals in discussion or voting
    When I try to submit a new amendment proposal
    Then I should receive an error message
    And my proposal should not be created
    And I should be informed about the limit on concurrent amendment proposals 