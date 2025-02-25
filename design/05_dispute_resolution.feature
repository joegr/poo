Feature: Dispute Resolution
  As a DAO member
  I want to have a fair dispute resolution process
  So that implementation issues can be addressed transparently

  Background:
    Given I am a verified DAO member
    And there is an executed proposal

  Scenario: Raise a dispute about proposal implementation
    Given a proposal was executed within the last 72 hours
    When I raise a dispute with the reason "Implementation deviates from proposal"
    Then the dispute should be recorded
    And the dispute should be assigned to the arbitration committee
    And the implementation should be temporarily paused

  Scenario: Select arbitration committee members
    Given it is time to select a new arbitration committee
    When the system randomly selects 31 members from the top 10% of token holders
    Then each selected member should be notified
    And the committee membership should be publicly visible
    And the committee should be active for the defined term

  Scenario: Vote on a dispute as committee member
    Given I am a member of the arbitration committee
    And there is an active dispute
    When I review the dispute details
    And I vote "UPHOLD" on the dispute
    Then my vote should be recorded
    And the dispute resolution progress should be updated

  Scenario: Resolve dispute in favor of the proposal
    Given there is an active dispute
    And a majority of the arbitration committee has voted
    And more than 50% of votes are "REJECT" (against the dispute)
    When the dispute voting period ends
    Then the dispute should be marked as "REJECTED"
    And the proposal implementation should continue
    And all parties should be notified of the outcome

  Scenario: Resolve dispute against the proposal
    Given there is an active dispute
    And a majority of the arbitration committee has voted
    And more than 50% of votes are "UPHOLD" (in favor of the dispute)
    When the dispute voting period ends
    Then the dispute should be marked as "UPHELD"
    And the proposal implementation should be reverted
    And all parties should be notified of the outcome

  Scenario: Dispute resolution timeout
    Given there is an active dispute
    And the voting period of 7 days has passed
    And less than a majority of committee members have voted
    When the system checks for expired disputes
    Then the dispute period should be extended by 3 days
    And committee members should be reminded to vote

  Scenario: Recuse from dispute resolution due to conflict of interest
    Given I am a member of the arbitration committee
    And there is an active dispute for a proposal I created
    When I declare a conflict of interest
    Then I should be recused from voting on this dispute
    And another committee member should be randomly selected as replacement

  Scenario: Appeal a dispute resolution
    Given a dispute has been resolved
    When I submit an appeal within 48 hours with new evidence
    Then the appeal should be recorded
    And a new arbitration committee should be formed
    And the appeal should follow the same resolution process 