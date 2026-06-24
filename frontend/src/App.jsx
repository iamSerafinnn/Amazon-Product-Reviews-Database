import { useState } from 'react'
import './App.css'

// Const Values - API URL Link, Page Size
// -----------------------------------------------------------------------
const API_URL = 'https://amazon-product-reviews-database-production.up.railway.app'
// const API_URL = 'http://127.0.0.1:8000'
// const API_URL = 'http://192.168.1.207:8000'
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
  // Extract the image of the product
  const imgUrl = ExtractImage(product.images)

  // Returning the product UI design
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

        {/* Image of Product */}
        {imgUrl && (
          <img
            src={imgUrl}
            alt={product.title}
            style={{ width: '100%', height: '180px', objectFit: 'contain', borderRadius: '6px', marginBottom: '8px', background: '#f9fafb' }}
          />)
        }

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
// ExtractImage() - Extract the image from a passed in image URL
// -----------------------------------------------------------------------
function ExtractImage(images) {
  // If image url is empty, return nothing
  if (!images) return null
  
  try {
    // Normalized the data. If images is already a JS object, use it as-is. 
    // If it's a string, parse it in a valid JS object.
    const normalized = typeof images === 'object'
      ? images
      : JSON.parse(images.replace(/'/g, '"').replace(/array\(\[/g, '[').replace(/\],\s*dtype=object\)/g, ']'))
    
    // Return the normalized image JS object.
    return normalized?.large?.[0] || normalized?.hi_res?.[0] || normalized?.thumb?.[0] || null
  
  // Error handling
  } catch {
    return null
  }
}


// -----------------------------------------------------------------------
// CleanText() - Cleans a passed in text by removing unecessary chars 
// and polishing it. Used to make clean product descriptions and text
// -----------------------------------------------------------------------
function CleanText(text) {
  if (!text) return ''
  return text
    .replace(/\[|\]/g, '')              // remove brackets
    .replace(/'([^']*?)'\s*'/g, '$1 ')  // remove repeated quoted items
    .replace(/'\s*'/g, ' ')             // remove adjacent quotes
    .replace(/^'|'$/g, '')              // remove leading/trailing quotes
    .replace(/\s+/g, ' ')               // collapse spaces
    .trim()
}


// -----------------------------------------------------------------------
// App() - Main full-stack component of the UI, stores the all the states
// and decides what to render in the UI
// -----------------------------------------------------------------------
function App() {

  // The state variables - When one of these variables changes
  // the react UI app changes
  // ------------------------------------------------------------
  const [query, setQuery] = useState('') 
  const [page, setPage] = useState(1)
  const [erTab, setERTab] = useState(1)

  const [results, setResults] = useState([])
  const [allResults, setAllResults] = useState([])

  const [error, setError] = useState(null)
  const [selectedProduct, setSelectedProduct] = useState(null)

  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [hasMore, setHasMore] = useState(false)
  const [modalLoading, setModalLoading] = useState(false)
  const [showER, setShowER] = useState(false)
  const [showOverview, setShowOverview] = useState(false)
  // ------------------------------------------------------------


  // ------------------------------------------------------------
  // handlePage() - Handles navigating the pagination of the
  // search results.
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
  // handleCardClick() - Handles the card clicking for the product
  // cards and creates a detailed modal out of it.
  // ------------------------------------------------------------
  async function handleCardClick(product_ID) {
    // Initialized the modal and product states
    setModalLoading(true)
    setSelectedProduct(null)

    // Loads product
    try {
      // Sends a get request to api.py and awaits response
      const res = await fetch(`${API_URL}/products/${product_ID}`)

      // Parses the product from the response into a JS object
      const data = await res.json()

      // Updates the selected product states
      setSelectedProduct(data)

    // Error Handling
    } catch (e) {
      console.error('Failed to load product: ', e)

    // Updates the modal loading state
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
            <span className="brand-name">EpicCode Amazon Product Database System</span>
          </div>

          {/* Header Sub-Text */}
          <p className="brand-sub">Query semantic search over Amazon product reviews</p>
          
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

              {/* Previous Button */}
              {page > 1 && (
                <button className="page-btn" onClick={() => handlePage(page - 1)}>
                  ← Previous
                </button>
              )}
              
              {/* Next Button */}
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
              {['headphones', 'laptop', 'TV', 'camera', 'phone', 'speaker'].map(s => (
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

            {/* Modal Loading Screen */}
            {modalLoading && <div className="modal-loading">Loading...</div>}
      
            {/* Modal of Selected Product */}
            {selectedProduct && (
              <>
              {/* Modal Border Styling */}
              <hr style={{ border: 'none', borderTop: '1px solid #7b7c7dff', margin: '16px 0' }} />

              {/* Modal X Close Button */}
              <button className="modal-close" style={{ position: 'sticky', bottom: '8px', float: 'right' }} onClick={() => setShowER(false)}>✕ Close</button>
                
              {/* Modal Header: Store and Price Tags */}
              <div className="modal-header">
                <span className="store-tag">{selectedProduct.store || 'Unknown Store'}</span>
                {selectedProduct.price && (
                  <span className="price">${parseFloat(selectedProduct.price).toFixed(2)}</span>
                )}
              </div>

              {/* Modal Product Title */}
              <h2 className="modal-title">{selectedProduct.title}</h2>

              {/* Modal Product Image */}
              {(() => {
                const imgUrl = ExtractImage(selectedProduct.images)
                return imgUrl ? (
                  <img
                    src={imgUrl}
                    alt={selectedProduct.title}
                    style={{ width: '100%', maxHeight: '280px', objectFit: 'contain', borderRadius: '8px', margin: '12px 0', background: '#f9fafb' }}
                  />
                ) : null
              })()}

              {/* Modal Product Rating and Reviews */}
              {selectedProduct.average_rating && (
                <div className="modal-rating">
                  <StarRating rating={selectedProduct.average_rating} />
                  <span className="review-count">
                    {selectedProduct.rating_number?.toLocaleString()} reviews
                  </span>
                </div>
              )}

              {/* Modal Product Description */}
              {selectedProduct.description && (
                <div className="modal-section">
                  <h4>Description</h4>
                  <p>{CleanText(selectedProduct.description)}</p>
                </div>
              )}

              {/* Modal Product Features */}
              {selectedProduct.features && (
                <div className="modal-section">
                  <h4>Features</h4>
                  <p>{CleanText(selectedProduct.features)}</p>
                </div>
              )}

              {/* Modal Product Details */}
              {selectedProduct.details && (
                <div className="modal-section">
                  <h4>Details</h4>
                  {(() => {
                    try {
                      const raw = typeof selectedProduct.details === 'string'
                        ? selectedProduct.details
                        : JSON.stringify(selectedProduct.details)
                      // Details Normalized Text
                      // Handle Python-style dict strings (single quotes, True/False/None)
                      const normalized = raw
                        .replace(/'/g, '"')
                        .replace(/True/g, 'true')
                        .replace(/False/g, 'false')
                        .replace(/None/g, 'null')
                      const parsed = JSON.parse(normalized)
                      return (
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                          <tbody>
                            {Object.entries(parsed).map(([key, val]) => (
                              <tr key={key} style={{ borderBottom: '1px solid #626363ff' }}>
                                <td style={{ padding: '6px 12px 6px 0', fontWeight: 600, whiteSpace: 'nowrap', verticalAlign: 'top', color: '#6b7280' }}>
                                  {key}
                                </td>
                                <td style={{ padding: '6px 0', verticalAlign: 'top', color: 'var(--muted)', fontSize: '0.875rem' }}>
                                  {String(val)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )
                    } catch {
                      // Fallback if parsing fails
                      return <p>{CleanText(selectedProduct.details).replace(/[{}]|\s+/g, ' ').trim()}</p>
                    }
                  })()}
                </div>
            )}
            </>
          )}
        </div>
      </div>
      )}

      {/* Fixed Bottom Bar */}
      <div className="bottom-bar">
        <button className="page-btn" onClick={() => setShowER(true)}>ER Diagram</button>
        <button className="page-btn" onClick={() => setShowOverview(true)}>Project Overview</button>
        <button className="page-btn" onClick={() => window.open('https://github.com/iamSerafinnn/Amazon-Product-Reviews-Database')}>GitHub Repo</button>
        <button className="page-btn" onClick={() => window.open('https://iamserafinnn.github.io/')}>My Portfolio</button>
      </div>

      {/* ER Diagram Modal */}
      {showER && (
        <div className="modal-overlay" onClick={() => setShowER(false)}>
          <div className="modal" style={{ maxWidth: '90vw', width: '90vw', maxHeight: '90vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowER(false)}>✕</button>
            <h2 className="modal-title">ER Diagram</h2>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
              <button className="page-btn" onClick={() => setERTab(1)}>Query ER Diagram</button>
              <button className="page-btn" onClick={() => setERTab(2)}>Database ER Diagram</button>
            </div>
            {erTab === 1 && <iframe src="/Amazon-Product-Reviews-Database/diagram.pdf" width="100%" height="800px" />}
            {erTab === 2 && <iframe src="/Amazon-Product-Reviews-Database/diagram2.pdf" width="100%" height="800px" />}
          </div>
        </div>
      )}

      {/* Overview Modal */}
      {showOverview && (
        <div className="modal-overlay" onClick={() => setShowOverview(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowOverview(false)}>✕</button>
            <h2 className="modal-title">Project Overview</h2>
            <div className="modal-section" style={{textAlign: 'left'}}>

              <hr style={{ border: 'none', borderTop: '1px solid #7b7c7dff', margin: '16px 0' }} />
              
              <h4>What did I build in this project?</h4>
              <p>
                This is a full-stack development of a semantic search query database of a dataset containing
                Amazon products along with their descriptions, prices, stores, and features of each product.
                This project is an implementation of an FAISS index database that converts raw JSON chunks
                and the user's input query into vector embeddings. It finds the most relevant products by
                returning the most similar embeddings of the input query to items in that database.
              </p>

              <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '16px 0' }} />

              <h4>How does my project work?</h4>
              <p>
                Product descriptions are just raw JSON text, then they are chunked, and are then converted
                into high-dimensional vectors using a SentenceTransformer model. Once converted, these 
                vector embeddings are stored in a FAISS, Facebook AI Similarity Search, index. These are
                optimized data structures that are used to store vector embeddings efficiently at a large
                scale. So, when you search in that text box, that search query is then converted into a 
                vector embedding as well and the FAISS index will find the closes matching products to that
                query.

                Importantly, I used a FastAPI, a high performing python web framework that translates incoming
                HTTP request from backend to frontend into actionable events. This is how I manage to allow
                communication between the backend and frontend part of this program.
              </p>

              <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '16px 0' }} />

              <h4>Tech Stack / What was used?</h4>
              <p>
                Frontend: React, CSS <br></br>
                Backend: Python, SQL <br></br>
                Important Frameworks: FASTAPI, FAISS, SentenceTransformers, PostgreSQL <br></br>
                Version Control: Git/GitHub <br></br>
                Development IDE: Visual Studios Code <br></br>
                Database Size: 500 Amazon products stored with ratings, images, pricing, and metadata. <br></br>
              </p>

              <hr style={{ border: 'none', borderTop: '1px solid #7b7c7dff', margin: '16px 0' }} />
              
            </div>
          </div>
        </div>
      )}
    
    </div>
  )
  // ------------------------------------------------------------
}

export default App
