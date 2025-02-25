Feature: API Gateway
  As a developer or client application
  I want to interact with the DAO governance system through a secure API gateway
  So that I can access services in a controlled and efficient manner

  Background:
    Given the API gateway is operational
    And I have valid API credentials

  Scenario: Authenticate with the API
    When I send an authentication request with valid credentials
    Then I should receive a JWT token
    And the token should contain appropriate claims and expiration
    And I should be able to use this token for subsequent requests

  Scenario: Access proposal endpoints
    Given I have a valid authentication token
    When I send a GET request to "/api/proposals"
    Then I should receive a 200 OK response
    And the response should contain a list of proposals
    And the response should be properly paginated

  Scenario: Create a new proposal through API
    Given I have a valid authentication token
    And I have sufficient governance tokens
    When I send a POST request to "/api/proposals" with valid proposal data
    Then I should receive a 201 Created response
    And the response should contain the created proposal details
    And the proposal should be visible in the system

  Scenario: Rate limiting prevents abuse
    Given I have a valid authentication token
    When I send more than 60 requests within a minute
    Then I should receive a 429 Too Many Requests response
    And the response should include a Retry-After header
    And my subsequent requests should be blocked until the rate limit resets

  Scenario: API request logging for auditing
    Given I have a valid authentication token
    When I send a request to modify a resource
    Then the request should be logged with the following details:
      | Timestamp | User ID | IP Address | Endpoint | Method | Response Code |
    And the logs should be securely stored for auditing purposes

  Scenario: Access control based on permissions
    Given I have a valid authentication token
    But I do not have guardian privileges
    When I send a request to a guardian-only endpoint
    Then I should receive a 403 Forbidden response
    And the response should explain the permission requirements

  Scenario: API versioning support
    Given the API supports multiple versions
    When I send a request with an "Accept-Version" header specifying version "1.2"
    Then I should receive a response compatible with version 1.2
    And if I request an unsupported version, I should receive an appropriate error

  Scenario: GraphQL API for complex queries
    Given I have a valid authentication token
    When I send a GraphQL query to fetch proposal details with related votes
    Then I should receive a 200 OK response
    And the response should contain exactly the requested data structure
    And the response should not include unnecessary fields

  Scenario: Real-time updates via subscriptions
    Given I have established a WebSocket connection to the API
    And I have subscribed to proposal updates
    When a proposal status changes
    Then I should receive a real-time notification with the updated details
    And the notification should be delivered within 1 second of the change

  Scenario: Secure treasury API access
    Given I am a guardian with appropriate permissions
    When I send a request to the treasury API endpoint
    Then the request should be routed through an encrypted channel
    And the request should require request signing
    And all operations should be comprehensively logged 