Feature: Treasury Management
  As a DAO member
  I want the treasury to be securely and effectively managed
  So that the organization remains financially stable and sustainable

  Background:
    Given I am a verified DAO member
    And the DAO has a multi-signature treasury wallet

  Scenario: View treasury assets and balances
    When I access the treasury dashboard
    Then I should see the current balance of all treasury assets
    And I should see the USD value of each asset
    And I should see the current reserve ratio
    And I should see the risk score for each asset

  Scenario: Create a treasury transaction proposal
    Given I hold at least 1% of the total governance tokens
    When I create a treasury transaction proposal with the following details:
      | Asset | Amount | Transaction Type | Description                  |
      | ETH   | 10     | WITHDRAWAL       | Fund development grant       |
    Then the transaction should be created with status "PENDING"
    And the transaction should require guardian approval

  Scenario: Approve a treasury transaction as a guardian
    Given I am one of the 9 elected guardians
    And there is a pending treasury transaction
    When I approve the transaction
    Then my approval should be recorded
    And the transaction approval count should increase by 1

  Scenario: Execute a treasury transaction with sufficient approvals
    Given there is a pending treasury transaction
    And 5 out of 9 guardians have approved the transaction
    When the transaction is executed
    Then the transaction status should change to "EXECUTED"
    And the treasury balance should be updated accordingly
    And the transaction should be recorded on the blockchain

  Scenario: Reject a treasury transaction
    Given I am one of the 9 elected guardians
    And there is a pending treasury transaction
    When I reject the transaction with reason "Excessive spending"
    Then my rejection should be recorded
    And if 5 out of 9 guardians reject, the transaction status should change to "REJECTED"

  Scenario: Maintain minimum reserve ratio
    Given the treasury has various assets
    When I check the treasury stability metrics
    Then at least 30% of treasury assets should be in stable assets
    And the system should alert if the reserve ratio falls below 30%

  Scenario: Apply counter-cyclical buffer
    Given the treasury is in a growth period
    When new revenue comes into the treasury
    Then a higher percentage should be allocated to reserves
    And when in contraction, reserves should be released according to the strategy

  Scenario: Enforce macro-prudential risk limits
    Given the treasury has an allocation strategy
    When I view the asset allocation
    Then no single asset class should exceed its maximum allocation percentage
    And the system should recommend rebalancing if limits are exceeded

  Scenario: Elect treasury guardians
    Given it is time for quarterly guardian elections
    When members vote for guardians using quadratic voting
    Then the top 9 candidates should be elected as guardians
    And they should have multi-signature control of the treasury
    And their term should be set for 3 months

  Scenario: Monitor treasury health indicators
    When I view the treasury health dashboard
    Then I should see key indicators including:
      | Indicator                | Status  |
      | Reserve Ratio            | Healthy |
      | Asset Diversification    | Healthy |
      | Liquidity Ratio          | Healthy |
      | Growth Rate              | Stable  |
      | External Dependency Risk | Low     | 