import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

/**
 * @typedef {Object} ContactInfo
 * @property {string} phone_number
 * @property {string} email
 * @property {string} physical_address
 */

/**
 * @typedef {Object} BusinessHours
 * @property {Object} monday
 * @property {string} monday.open
 * @property {string} monday.close
 * @property {Object} tuesday
 * @property {string} tuesday.open
 * @property {string} tuesday.close
 * @property {Object} wednesday
 * @property {string} wednesday.open
 * @property {string} wednesday.close
 * @property {Object} thursday
 * @property {string} thursday.open
 * @property {string} thursday.close
 * @property {Object} friday
 * @property {string} friday.open
 * @property {string} friday.close
 * @property {Object} saturday
 * @property {string} saturday.open
 * @property {string} saturday.close
 * @property {Object} sunday
 * @property {string} sunday.open
 * @property {string} sunday.close
 */

/**
 * @typedef {Object} SocialMediaProfile
 * @property {number} id
 * @property {string} platform
 * @property {string} handle
 * @property {string} url
 */

/**
 * @typedef {Object} FAQ
 * @property {number} id
 * @property {string} question
 * @property {string} answer
 */

/**
 * @typedef {Object} RestaurantLocation
 * @property {number} latitude
 * @property {number} longitude
 * @property {string} address
 * @property {string} city
 * @property {string} state
 * @property {string} zip
 * @property {string} country
 */

/**
 * @typedef {Object} ContactForm
 * @property {string} name
 * @property {string} email
 * @property {string} message
 */

/**
 * @typedef {Object} UploadFileResponse
 * @property {string} filename
 * @property {string} filetype
 * @property {number} filesize
 * @property {string} fileurl
 */

const ContactPage = () => {
  const [contactInfo, setContactInfo] = useState({});
  const [businessHours, setBusinessHours] = useState({});
  const [socialMediaProfiles, setSocialMediaProfiles] = useState([]);
  const [faq, setFaq] = useState([]);
  const [restaurantLocation, setRestaurantLocation] = useState({});
  const [contactForm, setContactForm] = useState({ name: '', email: '', message: '' });
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isFormSubmitted, setIsFormSubmitted] = useState(false);

  const getContactInfo = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/contact-info');
      setContactInfo(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  const getBusinessHours = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/business-hours');
      setBusinessHours(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  const getSocialMediaProfiles = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/social-media');
      setSocialMediaProfiles(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  const getFaq = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/faq');
      setFaq(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  const getRestaurantLocation = useCallback(async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/restaurant-location');
      setRestaurantLocation(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  const submitContactForm = useCallback(async (event) => {
    event.preventDefault();
    try {
      const response = await axios.post('http://localhost:5000/api/contact-form', contactForm);
      setIsFormSubmitted(true);
    } catch (error) {
      setError(error.message);
    }
  }, [contactForm]);

  const uploadFile = useCallback(async (event) => {
    try {
      const file = event.target.files[0];
      const formData = new FormData();
      formData.append('file', file);
      const response = await axios.post('http://localhost:5000/api/upload-file', formData);
      setFile(response.data);
    } catch (error) {
      setError(error.message);
    }
  }, []);

  useEffect(() => {
    getContactInfo();
    getBusinessHours();
    getSocialMediaProfiles();
    getFaq();
    getRestaurantLocation();
  }, [getContactInfo, getBusinessHours, getSocialMediaProfiles, getFaq, getRestaurantLocation]);

  const handleContactFormChange = useCallback((event) => {
    setContactForm({ ...contactForm, [event.target.name]: event.target.value });
  }, [contactForm]);

  const validateForm = useCallback(() => {
    if (!contactForm.name || !contactForm.email || !contactForm.message) {
      return false;
    }
    return true;
  }, [contactForm]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Contact Us</h1>
      <section>
        <h2>Contact Information</h2>
        <p>Phone: {contactInfo.phone_number}</p>
        <p>Email: {contactInfo.email}</p>
        <p>Address: {contactInfo.physical_address}</p>
      </section>
      <section>
        <h2>Business Hours</h2>
        <ul>
          {Object.keys(businessHours).map((day) => (
            <li key={day}>
              {day}: {businessHours[day].open} - {businessHours[day].close}
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h2>Social Media</h2>
        <ul>
          {socialMediaProfiles.map((profile) => (
            <li key={profile.id}>
              <a href={profile.url} target="_blank" rel="noopener noreferrer">
                {profile.platform} - {profile.handle}
              </a>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h2>FAQ</h2>
        <ul>
          {faq.map((question) => (
            <li key={question.id}>
              <h3>{question.question}</h3>
              <p>{question.answer}</p>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <h2>Restaurant Location</h2>
        <div>
          <iframe
            title="Restaurant Location"
            src={`https://www.google.com/maps/embed/v1/place?key=YOUR_API_KEY&q=${restaurantLocation.address}`}
            frameBorder="0"
            allowFullScreen
          />
        </div>
      </section>
      <section>
        <h2>Contact Form</h2>
        <form onSubmit={submitContactForm}>
          <label>
            Name:
            <input type="text" name="name" value={contactForm.name} onChange={handleContactFormChange} />
          </label>
          <label>
            Email:
            <input type="email" name="email" value={contactForm.email} onChange={handleContactFormChange} />
          </label>
          <label>
            Message:
            <textarea name="message" value={contactForm.message} onChange={handleContactFormChange} />
          </label>
          <input type="file" onChange={uploadFile} />
          <button type="submit" disabled={!validateForm() || isFormSubmitted}>
            {isFormSubmitted ? 'Form Submitted' : 'Submit'}
          </button>
        </form>
      </section>
    </div>
  );
};

export default ContactPage;
