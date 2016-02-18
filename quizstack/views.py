from quiz.models import SubCategory, Category, Quiz, Question
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import QuizStack
from .serializer import QuizStackSerializer

@api_view(['POST'])
def create_quizstack(request):
	try:
		serializer = QuizStackSerializer(data = request.data)
		if serializer.is_valid():
			serializer.save()
		else:
			return Response({ 'errors' : serializer.errors }, status = status.HTTP_400_BAD_REQUEST)
		return Response(serializer.data, status = status.HTTP_200_OK)
	except Exception as e:
		print e.args
		return Response({'errors' : 'Cannot add to the stack.'}, status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_quizstack(request, quiz_id, quizstack_id):
	if quizstack_id == 'all':
		try:
			quizstack_list = QuizStack.objects.filter(quiz=quiz_id).order_by('-id')
			serializer = QuizStackSerializer(quizstack_list, many = True)
			return Response(serializer.data, status = status.HTTP_200_OK)
		except QuizStack.DoesNotExist as e:
			print e.args
			return Response({'errors': 'Quiz Stack not found'}, status=status.HTTP_404_NOT_FOUND)
	elif quizstack_id.isnumeric():
		try:
			quizstack = QuizStack.objects.get(id = quizstack_id, quiz=quiz_id)
			serializer = QuizStackSerializer(quiz, many=False)
			return Response(serializer.data, status = status.HTTP_200_OK)
		except QuizStack.DoesNotExist as e:
			return Response({'errors': 'Quiz Stack not found'}, status = status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
def delete_quizstack(request, quiz_id, quizstack_id):
	if quizstack_id == 'all':
		try:
			quizstack_list = QuizStack.objects.filter(quiz=quiz_id)
			for quizstack in quizstack_list:
				quizstack.delete()
			return Response(status = status.HTTP_200_OK)
		except QuizStack.DoesNotExist as e:
			print e.args
			return Response({'errors': 'Quiz Stack not found'}, status=status.HTTP_404_NOT_FOUND)
	elif quizstack_id.isnumeric():
		try:
			quizstack = QuizStack.objects.get(id = quizstack_id, quiz=quiz_id)
			quizstack.delete()
			return Response(status = status.HTTP_200_OK)
		except QuizStack.DoesNotExist as e:
			return Response({'errors': 'Quiz Stack not found'}, status = status.HTTP_404_NOT_FOUND)
