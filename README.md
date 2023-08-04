# TicketOverflow

This is a backend ticket application designed to handle thousands of concurrent users per second for the course CSSE6400 at the University of Queensland. This application's primary purpose to accept user requests via endpoints to purchase ticket, generate tickets, form concerts and view seating within concerts. The significant design challenge is that generating tickets and concert seating plans is extremely work intensive requiring a few seconds and 20+ seconds respectively. This quickly becomes an issue when thousands of users are doing this at the same time.

Due to this design challenge a quart backend was made making it fully asychronous. To further decrease latency a redis cache was utilised to store commonly accessed data while a no sql database (dynamoDB) was used for consistent storage. This application is designed to be deployed to AWS via terraform and consists of:

- 2 ECS clusters
    - One cluster dedicated to ticket generation
    - One cluster dedicated to handling user requests
- Elasticache (Redis)
- DynamoDB
- Simple Queue Service (SQS) 

To test this application k6 was used which puts signifcant load on the server. After testing the designed application was able to handle 3000+ concurrent requests per second due to it's autoscaling and deployment. The upper bound of the number of requests per second is unknown due to hardware limitations. 