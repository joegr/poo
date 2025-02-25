"""
GraphQL schema for dao_governance project.
"""

import graphene
import graphql_jwt

class Query(graphene.ObjectType):
    """Root query for the GraphQL API."""
    # This will be extended by the queries from each app
    pass

class Mutation(graphene.ObjectType):
    """Root mutation for the GraphQL API."""
    # JWT authentication mutations
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    
    # This will be extended by the mutations from each app
    pass

schema = graphene.Schema(query=Query, mutation=Mutation) 