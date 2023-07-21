  const processSteps = document.querySelectorAll('.process-step');

  // Intersection Observer options
  const observerOptions = {
    rootMargin: '0px',
    threshold: 0.5 // Adjust this value for the desired trigger point when scrolling to the div
  };

  // Callback function for the Intersection Observer
  function handleIntersect(entries, observer) {
    entries.forEach((entry, index) => {
      if (entry.intersectionRatio > 0) {
        setTimeout(() => {
          entry.target.classList.add('show');
        }, 200 * index); // Adjust the delay (in milliseconds) between each element
      }
    });
  }

  // Create an Intersection Observer instance
  const observer = new IntersectionObserver(handleIntersect, observerOptions);

  // Observe each process step
  processSteps.forEach(step => {
    observer.observe(step);
  });