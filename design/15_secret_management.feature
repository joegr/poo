Feature: Secret Management with HashiCorp Vault
  As a DAO platform operator
  I want to securely manage secrets and credentials
  So that sensitive information is protected throughout the system

  Background:
    Given the DAO governance system is operational
    And HashiCorp Vault is deployed and initialized

  Scenario: Store application secrets in Vault
    Given I have sensitive application credentials
    When I store the credentials in Vault
    Then the credentials should be encrypted at rest
    And access to the credentials should require authentication
    And all access attempts should be logged

  Scenario: Retrieve secrets from application services
    Given an application service needs to access a database
    When the service starts up
    Then it should authenticate with Vault using its service account
    And it should retrieve only the specific credentials it needs
    And the credentials should be automatically rotated according to policy

  Scenario: Implement secret rotation policies
    Given I have defined rotation policies for different types of secrets
    When the rotation period for a secret expires
    Then Vault should automatically generate a new secret
    And the new secret should be distributed to authorized services
    And the old secret should be revoked after a grace period

  Scenario: Manage encryption keys
    Given I need to encrypt sensitive data
    When I request an encryption key from Vault
    Then Vault should provide a managed encryption key
    And the encryption operation should be performed using the key
    And the key should never be exposed to the application directly

  Scenario: Implement transit encryption service
    Given I have data that needs to be encrypted
    When I send the data to Vault's transit encryption service
    Then Vault should encrypt the data using a managed key
    And return the encrypted data
    And I should be able to decrypt the data using the same service
    And the encryption keys should remain secured within Vault

  Scenario: Set up Vault high availability
    Given Vault is deployed across multiple nodes
    When a primary Vault node fails
    Then a secondary node should be automatically promoted
    And services should reconnect to the new primary node
    And no secrets should be lost during the failover

  Scenario: Implement secret access policies
    Given different services require different levels of access
    When I define access policies in Vault
    Then each service should only access secrets within its policy scope
    And attempts to access unauthorized secrets should be denied and logged
    And policy changes should require multi-person approval

  Scenario: Audit secret access
    Given auditing is enabled in Vault
    When a secret is accessed
    Then the access should be recorded in the audit log
    And the log should include who accessed the secret
    And the log should include when the secret was accessed
    And the log should include which secret was accessed

  Scenario: Integrate with Kubernetes service accounts
    Given the application runs in Kubernetes
    When a pod starts with a Kubernetes service account
    Then the pod should authenticate to Vault using its service account token
    And Vault should validate the token with Kubernetes
    And grant access based on the pod's identity and namespace

  Scenario: Recover from disaster scenarios
    Given Vault is configured with disaster recovery capabilities
    When a catastrophic failure occurs
    Then the recovery process should be initiated using unseal keys
    And the recovery should require a quorum of key holders
    And the recovered Vault should have all the original secrets
    And the recovery process should be thoroughly documented and tested 