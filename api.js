import axios from 'axios';

const API_URL = "http://localhost:8000";

export const logInteraction = (userInput) => {
    return axios.post(`${API_URL}/log-interaction`, { user_input: userInput });
};