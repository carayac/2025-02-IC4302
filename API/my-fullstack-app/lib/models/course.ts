import mongoose, { Schema, Model, Document } from 'mongoose'

// Interfaz para las reviews
interface IReview {
  user: string
  comment: string | null
  rating: number
  date: string
}

// Interfaz para el documento/curso
export interface ICourse extends Document {
  _id: mongoose.Types.ObjectId
  title: string
  description: string | null
  'short-description': string
  general_category: string
  specific_category: null
  image: string
  price: number
  currency: string
  language: string
  students: number
  certificate_info: string
  authorComment: string
  reviews: IReview[]
  rating_value: number
  date_extracted: null
  '1': string | null
}

// Schema de Review para validar los datos a la hora de guardarlos en la base de datos
const ReviewSchema = new Schema<IReview>(
  {
    user: {
      type: String,
      required: true,
    },
    comment: {
      type: String,
      default: null,
    },
    rating: {
      type: Number,
      required: true,
      min: 0,
      max: 5,
    },
    date: {
      type: String,
      required: true,
    },
  },
  { _id: false }
)

// Schema del Curso para validar los datos a la hora de guardarlos en la base de datos
const CourseSchema = new Schema<ICourse>(
  {
    title: {
      type: String,
      required: true,
    },
    description: {
      type: String,
      default: null,
    },
    'short-description': {
      type: String,
      required: true,
    },
    general_category: {
      type: String,
      required: true,
    },
    specific_category: {
      type: Schema.Types.Mixed,
      default: null,
    },
    image: {
      type: String,
      required: true,
    },
    price: {
      type: Number,
      required: true,
      min: 0,
    },
    currency: {
      type: String,
      required: true,
    },
    language: {
      type: String,
      required: true,
    },
    students: {
      type: Number,
      required: true,
      min: 0,
    },
    certificate_info: {
      type: String,
      required: true,
    },
    authorComment: {
      type: String,
      required: true,
    },
    reviews: {
      type: [ReviewSchema],
      default: [],
    },
    rating_value: {
      type: Number,
      required: true,
      min: 0,
      max: 5,
    },
    date_extracted: {
      type: Schema.Types.Mixed,
      default: null,
    },
    '1': {
      type: String,
      default: null,
    },
  },
  {
    collection: 'documents',
    timestamps: false,
  }
)

const Course: Model<ICourse> =
  mongoose.models.Course || mongoose.model<ICourse>('Course', CourseSchema)

export default Course