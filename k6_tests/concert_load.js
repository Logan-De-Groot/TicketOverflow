

import http from 'k6/http';
import { check, group, sleep } from 'k6';

const BASE_URL = 'http://localhost:6400/api/v1/concerts';

export const options = {
    stages: [
        { duration: '1m', target: 100 },
        { duration: '2m', target: 200 },
        { duration: '1m', target: 100 },
    ],
};

export default function () {
    group('concert endpoints', function () {
        let res;

        // Create a concert
        res = http.post(BASE_URL, JSON.stringify(generateRandomConcert()), {
            headers: { 'Content-Type': 'application/json' },
        });
        check(res, { 'status was 200': (r) => r.status === 200 });

        // Get all concerts
        res = http.get(BASE_URL);
        check(res, { 'status was 200': (r) => r.status === 200 });

        // Get a random concert ID
        const concerts = JSON.parse(res.body);
        const randomIndex = Math.floor(Math.random() * concerts.length);
        const concertId = concerts[randomIndex].id;

        // Get concert details
        res = http.get(`${BASE_URL}/${concertId}`);
        check(res, { 'status was 200': (r) => r.status === 200 });
    });

    sleep(1);
}

function generateRandomConcert() {
    const venues = ['Venue A', 'Venue B', 'Venue C'];
    const statuses = ['scheduled', 'cancelled', 'postponed'];
    const randomDate = new Date(Date.now() + Math.floor(Math.random() * 1000000000)).toISOString();

    return {
        name: `Concert ${Math.random().toString(36).substr(2, 5)}`,
        venue: venues[Math.floor(Math.random() * venues.length)],
        date: randomDate,
        capacity: Math.floor(Math.random() * 10000),
        status: statuses[Math.floor(Math.random() * statuses.length)],
    };
}