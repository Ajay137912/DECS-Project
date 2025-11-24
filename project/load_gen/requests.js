import http from 'k6/http';
import { check } from 'k6';

let counter = 0;

export let options = {
    vus: __ENV.VUS,
    duration: '20s',
};

export default function () {
    let r = Math.random();

    if (r < 0.7) {
        // 70% GET
        let res = http.get('http://localhost:1234/val?id=100');
        check(res, {
            'status ok/404': (r) => r.status === 200 || r.status === 404,
        });
    } else {
        // 30% SET
        counter++;
        let id = counter;
        let res = http.post(`http://localhost:1234/save?id=${id}&value=hello`);
        check(res, {
            'set ok': (r) => r.status === 200,
        });
    }
}