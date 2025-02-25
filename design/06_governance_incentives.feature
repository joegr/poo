Feature: Governance Incentives
  As a DAO member
  I want to be incentivized for active participation
  So that the governance system remains engaged and effective

  Background:
    Given I am a verified DAO member
    And I have governance tokens

  Scenario: Receive participation rewards for voting
    Given there is a proposal in "VOTING" status
    When I cast a vote on the proposal
    And the voting period ends
    Then I should receive additional governance tokens as reward
    And the reward should be proportional to my participation rate

  Scenario: Calculate participation rate
    Given there were 10 proposals in the last quarter
    And I voted on 8 of those proposals
    When my participation rate is calculated
    Then my participation rate should be 80%
    And my rewards should be calculated based on this rate

  Scenario: Lock tokens after voting
    Given there is a proposal in "VOTING" status
    When I cast a vote on the proposal
    Then my governance tokens should be locked for 30 days
    And I should not be able to transfer these tokens during the lock period
    And I should still be able to vote with locked tokens

  Scenario: Unlock tokens after lock period
    Given I have governance tokens that were locked 30 days ago
    When the lock period expires
    Then my tokens should be automatically unlocked
    And I should be able to transfer them again

  Scenario: Receive higher rewards for consistent participation
    Given I have participated in governance for 6 consecutive months
    And my average participation rate is above 90%
    When quarterly rewards are distributed
    Then I should receive a loyalty multiplier on my rewards
    And the multiplier should increase my rewards by at least 20%

  Scenario: Forfeit rewards due to inactivity
    Given I have not participated in any governance votes for 3 months
    When quarterly rewards are distributed
    Then I should not receive any participation rewards
    And I should be notified about my inactivity
    And I should be encouraged to participate in future votes

  Scenario: Earn reputation points through participation
    Given I actively participate in governance
    When I vote on proposals
    And I create quality proposals that pass
    And I contribute to discussions
    Then I should earn reputation points
    And my reputation score should be visible to other members
    And high reputation should grant me additional privileges

  Scenario: Receive rewards for proposal creation
    Given I create a proposal
    And the proposal passes voting
    And the proposal is successfully implemented
    When rewards are calculated
    Then I should receive a proposal creation bonus
    And the bonus should be higher for proposals with significant positive impact 