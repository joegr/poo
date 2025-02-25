Feature: Proposal Management
  As a DAO member
  I want to create, discuss, and vote on governance proposals
  So that the community can make collective decisions

  Background:
    Given I am a verified DAO member
    And I have governance tokens

  Scenario: Submit a new proposal
    Given I hold at least 1% of the total governance tokens
    When I submit a new proposal with the following details:
      | Title                    | Description                       | Rationale                         | Implementation Details            | Timeline                          |
      | Treasury Diversification | Diversify treasury into stablecoins | Reduce volatility during bear market | Convert 20% of ETH to USDC | 7 days for execution after approval |
    Then the proposal should be created with status "DRAFT"
    And the proposal should be visible to all DAO members

  Scenario: Start discussion period for a proposal
    Given I am the creator of a proposal with status "DRAFT"
    When I initiate the discussion period
    Then the proposal status should change to "DISCUSSION"
    And a 14-day discussion timer should start
    And all members should be able to comment on the proposal

  Scenario: Comment on a proposal during discussion
    Given there is a proposal in "DISCUSSION" status
    When I add a comment "I support this proposal because it reduces risk"
    Then my comment should be visible to all members
    And the comment should be associated with the proposal

  Scenario: Start voting period after discussion
    Given I am the creator of a proposal with status "DISCUSSION"
    And the 14-day discussion period has ended
    When I initiate the voting period
    Then the proposal status should change to "VOTING"
    And a 7-day voting timer should start

  Scenario: Cast votes using quadratic voting
    Given there is a proposal in "VOTING" status
    And I have 100 voting credits
    When I cast 5 votes in favor of the proposal
    Then 25 voting credits should be deducted from my balance
    And the proposal should record 5 votes in favor from me
    And my governance tokens should be locked for 30 days

  Scenario: Proposal passes with supermajority
    Given there is a proposal in "VOTING" status
    And the voting period has ended
    And at least 45% of all possible voting credits were used
    And at least 70% of votes are in favor
    When the voting results are tallied
    Then the proposal status should change to "APPROVED"
    And the proposal should enter a 48-hour timelock period

  Scenario: Proposal fails due to insufficient quorum
    Given there is a proposal in "VOTING" status
    And the voting period has ended
    And less than 45% of all possible voting credits were used
    When the voting results are tallied
    Then the proposal status should change to "REJECTED"
    And the proposal cannot be executed

  Scenario: Execute an approved proposal
    Given there is a proposal with status "APPROVED"
    And the 48-hour timelock period has passed
    When the proposal is executed
    Then the proposal status should change to "EXECUTED"
    And the proposed changes should be implemented
    And the execution should be recorded on the blockchain

  Scenario: Emergency cancellation during timelock
    Given there is a proposal with status "APPROVED"
    And the 48-hour timelock period has not yet passed
    When 75% of voting credits vote for cancellation
    Then the proposal status should change to "CANCELLED"
    And the proposal cannot be executed