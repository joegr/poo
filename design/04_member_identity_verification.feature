Feature: Member Identity Verification
  As a DAO
  I want to verify the identity of members
  So that Sybil attacks can be prevented

  Background:
    Given I am a user who wants to participate in the DAO

  Scenario: Register as a new member
    When I register with the following information:
      | Username | Email           | Wallet Address                             |
      | alice    | alice@test.com  | 0x1234567890abcdef1234567890abcdef12345678 |
    Then my account should be created
    And I should be prompted to complete identity verification
    And I should not be able to vote until verification is complete

  Scenario: Complete basic identity verification
    Given I have registered as a member
    When I complete the basic verification process by providing:
      | Full Name     | Date of Birth | Country       | ID Document Type | ID Document Number |
      | Alice Johnson | 1990-01-15    | United States | Passport         | AB123456          |
    Then my verification status should be updated to "PENDING_REVIEW"
    And my verification request should be queued for review

  Scenario: Pass identity verification review
    Given I have submitted my verification documents
    And a verification officer reviews my submission
    When the officer approves my verification
    Then my verification status should be updated to "VERIFIED"
    And I should be granted full participation rights in the DAO
    And I should be able to vote on proposals

  Scenario: Fail identity verification review
    Given I have submitted my verification documents
    And a verification officer reviews my submission
    When the officer rejects my verification with reason "Documents unclear"
    Then my verification status should be updated to "REJECTED"
    And I should receive notification with the rejection reason
    And I should be able to resubmit with corrected documents

  Scenario: Verify through third-party identity provider
    Given I have registered as a member
    When I choose to verify through a supported third-party provider
    And I complete the third-party verification flow
    And the provider confirms my identity
    Then my verification status should be updated to "VERIFIED"
    And I should be granted full participation rights in the DAO

  Scenario: Detect duplicate identity attempt
    Given there is a verified member with ID document "AB123456"
    When I try to register with the same ID document number
    Then I should receive an error message
    And my verification attempt should be flagged for review
    And suspicious activity should be logged

  Scenario: Periodic reverification requirement
    Given I am a verified member
    And my verification was completed 11 months ago
    When I log into the platform
    Then I should be notified that reverification is required within 1 month
    And if I don't reverify within 1 month, my voting rights should be suspended

  Scenario: Verification status check by the system
    Given there is a proposal in "VOTING" status
    When I attempt to cast a vote
    Then the system should check my verification status
    And if I am verified, my vote should be accepted
    And if I am not verified, my vote should be rejected with an explanation 