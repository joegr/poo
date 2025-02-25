Feature: Blockchain Integration
  As a DAO
  I want to integrate with a custom blockchain implementation
  So that governance operations are transparent, immutable, and verifiable

  Background:
    Given the DAO governance system is operational
    And the custom blockchain node is running

  Scenario: Record proposal creation on blockchain
    Given I am a verified DAO member
    When I create a new governance proposal
    Then the proposal details should be recorded on the blockchain
    And the transaction should include the proposal hash and metadata
    And the blockchain record should be linked to the proposal in the database

  Scenario: Record votes on blockchain
    Given there is an active proposal in voting phase
    When I cast a vote on the proposal
    Then my vote should be recorded on the blockchain
    And the transaction should include the vote direction and weight
    And the vote should be verifiable by any member

  Scenario: Execute proposal through smart contract
    Given a proposal has been approved
    And the timelock period has passed
    When the proposal is executed
    Then the execution should be processed through a smart contract
    And the transaction should update the relevant on-chain state
    And the execution should be recorded in the blockchain history

  Scenario: Verify proposal status from blockchain
    Given there is a proposal in the system
    When I query the blockchain for the proposal status
    Then I should receive the current status of the proposal
    And the status should match what is shown in the user interface
    And I should be able to verify the entire proposal history

  Scenario: Treasury transaction execution on blockchain
    Given there is an approved treasury transaction
    When the transaction is executed
    Then the funds should be transferred on the blockchain
    And the transaction should be signed by the required number of guardians
    And the transaction hash should be recorded in the system

  Scenario: Verify member voting power from blockchain
    Given I am a verified DAO member
    When I query my voting power
    Then the system should check my token balance on the blockchain
    And my voting power should be calculated based on my verified token holdings
    And any delegated voting power should be included in the calculation

  Scenario: Synchronize off-chain and on-chain state
    Given there is a temporary network disruption
    When the connection to the blockchain is restored
    Then the system should synchronize any pending transactions
    And the off-chain database should be updated to match the blockchain state
    And any discrepancies should be logged and resolved

  Scenario: Validate governance token transfers
    Given I hold governance tokens
    When I transfer tokens to another member
    Then the transfer should be recorded on the blockchain
    And if my tokens are locked for voting, the transfer should be rejected
    And my updated token balance should be reflected in the governance system

  Scenario: Process blockchain events
    Given the system listens for relevant blockchain events
    When a governance-related event occurs on the blockchain
    Then the event should be captured by the event processor
    And the system should update its state based on the event
    And relevant notifications should be sent to affected members

  Scenario: Provide cryptographic proof of governance actions
    Given a governance action has been executed
    When I request verification of the action
    Then I should receive a cryptographic proof of the action
    And the proof should be verifiable against the blockchain
    And the verification should not require trust in the governance platform 