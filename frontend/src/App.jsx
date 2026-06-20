import { useState } from 'react'
import './App.css'

// Const Values - API URL Link, Page Size
// -----------------------------------------------------------------------
const API_URL = 'http://127.0.0.1:8000'
const PAGE_SIZE = 10
// -----------------------------------------------------------------------


// -----------------------------------------------------------------------
// StarRating() - Fills in star rating based on a passed in product
// rating value
// -----------------------------------------------------------------------
function StarRating({ rating }) {
  // Total amount of starts to fill, double values must be rounded
  const stars = Math.round(rating)

  // Displays the number of stars and rating number on the UI
  return (
    <span className="stars">
      {'★'.repeat(stars)}{'☆'.repeat(5 - stars)}
      <span className="rating-number">{rating?.toFixed(1)}</span>
    </span>
  )
}

// -----------------------------------------------------------------------
// ProductCard() - Renders a product card into the UI based on the passed
// in dictionary of product storing its values
// -----------------------------------------------------------------------
function ProductCard({ product, onClick }) {
  return (
    <div className="card" onClick={onClick} style={{cursor: 'pointer'}}>
      <div className="card-header">

        {/* Store Name - Converts to unknown if empty */}
        <span className="store-tag">{product.store || 'Unknown Store'}</span>

        {/* Price of Product - Must be rounded to nearest 2 */}
        {product.price && (
          <span className="price">${parseFloat(product.price).toFixed(2)}</span>
        )}
      </div>

      {/* Product Name and Description  */}
      <h3 className="card-title">{product.title}</h3>
      <p className="card-description">{product.description}</p>

      {/* Product Ratings */}
      <div className="card-footer">
        {product.average_rating && (
          <StarRating rating={product.average_rating} />
        )}
        {product.rating_number && (
          <span className="review-count">
            {product.rating_number.toLocaleString()} reviews
          </span>
        )}
      </div>
    </div>
  )
}


// -----------------------------------------------------------------------
// App() - Main full-stack component of the UI, stores the all the states
// and decides what to render in the UI
// -----------------------------------------------------------------------
function App() {

  // The state variables - When one of these variables changes
  // the react UI app changes
  // _____________________________________________
  const [query, setQuery] = useState('') 
  const [page, setPage] = useState(1)

  const [results, setResults] = useState([])
  const [allResults, setAllResults] = useState([])

  const [error, setError] = useState(null)
  const [selectedProduct, setSelectedProduct] = useState(null)

  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [hasMore, setHasMore] = useState(false)
  const [modalLoading, setModalLoading] = useState(false)
  // _____________________________________________


  // ------------------------------------------------------------
  // handlePage() -
  // ------------------------------------------------------------
  function handlePage(newPage) {

    // Start Page and End Page
    const start = (newPage - 1) * PAGE_SIZE
    const end = start + PAGE_SIZE

    // Setting the results
    setResults(allResults.slice(start,end))
    setPage(newPage)
    setHasMore(end < allResults.length)
  }
  // ------------------------------------------------------------


  // ------------------------------------------------------------
  // handleCardClick() -
  // ------------------------------------------------------------
  async function handleCardClick(product_ID) {
    setModalLoading(true)
    setSelectedProduct(null)

    try {

      const res = await fetch(`${API_URL}/products/${product_ID}`)
      const data = await res.json()

      setSelectedProduct(data)

    } catch (e) {
      console.error('Failed to load product: ', e)

    } finally {
      setModalLoading(false)
    }
  }
  // ------------------------------------------------------------


  // ------------------------------------------------------------
  // handleSearch() - Function to handle search in database
  // ------------------------------------------------------------
  async function handleSearch(e, pageNum = 1) {

    // Stops browser from refreshing page with preventDefault()
    e.preventDefault()

    // A query can't be empty, stop if it is
    if (!query.trim()) return

    // Sets loading, error, and searched after searching
    setLoading(true)
    setError(null)
    setSearched(true)
    setPage(1)

    try {
      // Sending HTTP requst to Fast API server and waits for a response
      // and parse the JSON file if no error occurs
      const res = await fetch(`${API_URL}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim(), k: 100, user_id: 1 }),
      })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)

      // Retrieve the JSON file from the response
      const data = await res.json()

      // Set the results based on the data retrieved
      setAllResults(data.results)
      setResults(data.results.slice(0, PAGE_SIZE))
      setHasMore(data.results.length > PAGE_SIZE)

    // Error Handling
    } catch (err) {
      setError('Could not reach the search server. Make sure the API is running.')
      setResults([])
      setAllResults([])

    // Bring loading back to default after processing
    } finally {
      setLoading(false)
    }
  }
  // ------------------------------------------------------------


  // ------------------------------------------------------------
  // RETURN - BUILD THE UI
  // ------------------------------------------------------------
  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-inner">

          {/* Header Title */}
          <div className="brand">
            <span className="brand-icon">◈</span>
            <span className="brand-name">EpicCode Amazon Product Database</span>
          </div>

          {/* Header Sub-Text */}
          <p className="brand-sub">Semantic search over Amazon product reviews</p>
          
        </div>
      </header>

      {/* Search */}
      <section className="search-section">
        <form className="search-form" onSubmit={handleSearch}>

          {/* Search Box */}
          <div className="search-bar">

            {/* Search Text */}
            <input
              type="text"
              className="search-input"
              placeholder="Search for products..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading}
            />

            {/* Submit Button */}
            <button
              type="submit"
              className="search-btn"
              disabled={loading || !query.trim()}
            >
              {/* Loading */}
              {loading ? 'Searching...' : 'Search'}
            </button>

          </div>
        </form>
      </section>

      {/* Results */}
      <main className="results-section">

        {/* Error Result */}
        {error && (
          <div className="error-banner">
            {error}
          </div>
        )}

        {/* Loading Result */}
        {loading && (
          <div className="loading">
            <div className="spinner" />
            <p>Finding the best matches...</p>
          </div>
        )}

        {/* Empty Result */}
        {!loading && searched && results.length === 0 && !error && (
          <div className="empty">
            <p>No results found for <strong>"{query}"</strong>. Try a different search.</p>
          </div>
        )}

        {/* Product Result Section*/}
        {!loading && results.length > 0 && (
          <>

            {/* Total Product Results Feedback*/}
            <p className="results-meta">
              Page {page} of {Math.ceil(allResults.length / PAGE_SIZE)} — {allResults.length} results for <strong>"{query}"</strong>
            </p>

            {/* Product Results Grid */}
            <div className="results-grid">
              {results.map((product) => (
                <ProductCard 
                  key={product.product_id}
                  product={product}
                  onClick={(e) => {e.stopPropagation(); handleCardClick(product.product_id);}}
                />
              ))}
            </div>

            {/* Product Pagination */}
            <div className="pagination">
              {page > 1 && (
                <button className="page-btn" onClick={() => handlePage(page - 1)}>
                  ← Previous
                </button>
              )}
              {/* Next Button (Has More) */}
              {hasMore && (
                <button className="page-btn" onClick={() => handlePage(page + 1)}>
                  Next →
                </button>
              )}
            </div>

          </>
        )}

        {/* Empty Search Result */}
        {!searched && (
          <div className="empty-state">
            <p>Enter a search term to find products using semantic search.</p>
            <div className="suggestions">
              {['wireless headphones', 'gaming laptop', 'smart TV', '4K camera'].map(s => (
                <button
                  key={s}
                  className="suggestion-chip"
                  onClick={() => { setQuery(s) }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Product Detail Modal */}
      {(selectedProduct || modalLoading) && (
        <div className="modal-overlay" onClick={() => setSelectedProduct(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>

            {modalLoading && <div className="modal-loading">Loading...</div>}
      
            {selectedProduct && (
              <>
                <button className="modal-close" onClick={() => setSelectedProduct(null)}>✕</button>
                
                <div className="modal-header">
                  <span className="store-tag">{selectedProduct.store || 'Unknown Store'}</span>
                  {selectedProduct.price && (
                    <span className="price">${parseFloat(selectedProduct.price).toFixed(2)}</span>
                  )}
                </div>

                <h2 className="modal-title">{selectedProduct.title}</h2>

                {selectedProduct.average_rating && (
                  <div className="modal-rating">
                    <StarRating rating={selectedProduct.average_rating} />
                    <span className="review-count">
                      {selectedProduct.rating_number?.toLocaleString()} reviews
                    </span>
                  </div>
                )}

                {selectedProduct.description && (
                  <div className="modal-section">
                    <h4>Description</h4>
                    <p>{selectedProduct.description}</p>
                  </div>
                )}

                {selectedProduct.features && (
                  <div className="modal-section">
                    <h4>Features</h4>
                    <p>{selectedProduct.features}</p>
                  </div>
                )}

                {selectedProduct.details && (
                  <div className="modal-section">
                    <h4>Details</h4>
                    <p>{selectedProduct.details}</p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    
    </div>
  )
  // ------------------------------------------------------------
}

export default App
