resource "aws_dynamodb_table" "concerts" {
    name = "concerts"
    hash_key = "id"
    billing_mode = "PAY_PER_REQUEST"

    attribute {
        name = "id"
        type = "S"
    }  
}

resource "aws_dynamodb_table" "tickets" {
    name = "tickets"
    hash_key = "id"
    billing_mode = "PAY_PER_REQUEST"

    attribute {
        name = "id"
        type = "S"
    } 
}

resource "aws_dynamodb_table" "tickets_svg" {
    name = "tickets_svg"
    hash_key = "id"
    billing_mode = "PAY_PER_REQUEST"

    attribute {
        name = "id"
        type = "S"
    } 
}

resource "aws_dynamodb_table" "users" {
    name = "users"
    hash_key = "id"
    billing_mode = "PAY_PER_REQUEST"

    attribute {
        name = "id"
        type = "S"
    } 
}

resource "aws_dynamodb_table" "concerts_svg" {
    name = "concerts_svg"
    hash_key = "id"
    billing_mode = "PAY_PER_REQUEST"

    attribute {
        name = "id"
        type = "S"
    } 
}

resource "aws_sqs_queue" "ticket_queue" {
    name = "tickets"
}


resource "aws_sqs_queue" "concert_queue" {
    name = "concerts"
}
