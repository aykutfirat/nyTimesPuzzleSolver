#by Aykut Firat November 2015
import matplotlib.patches as patches
import pylab
import copy
import time
from random import randint, shuffle


class KnightsTour:

    def __init__(self, rows, cols, startTime, animate=False):
        self.rows = rows
        self.cols = cols
        self.size = self.rows* self.cols
        self.goalLength = self.size
        self.startTime = startTime
        self.animate=animate


    def gridLoc(self,i,j):
        if i < 0 or i>= self.rows or j<0 or j>=self.cols: return None
        return i*self.cols+j


    def gridij(self,x, extra=0):
        i = x // self.cols
        j = x - i * self.cols
        return j+extra,i+extra

    def possibleMoves(self,i,j):
        return [(i-1,j-2),(i-1,j+2),(i+1,j-2),(i+1,j+2),(i-2,j-1),(i-2,j+1),(i+2,j-1),(i+2,j+1)]


    def draw(self,path, title):
        for k,v in path:
            pylab.gca().add_patch(patches.Polygon([self.gridij(k,0.5),self.gridij(v,0.5)],closed=False,fill=True))
        pylab.grid()
        pylab.xticks(range(self.cols))
        pylab.yticks(range(self.rows))
        pylab.ylim((self.rows,0))
        pylab.xlim((0,self.cols))
        pylab.title(title)
        pylab.show()


    def getPossibilitiesMap(self):
        posMap = {}
        for i in range(self.rows):
            for j in range(self.cols):
                posMap[self.gridLoc(i,j)] = [self.gridLoc(mi,mj) for mi,mj in self.possibleMoves(i,j) if self.gridLoc(mi,mj) != None]
        return posMap

    def convertPossibilitiesToTuples(self,posMap):
        tuplePosMap = {}
        for k,v in posMap.iteritems():
            tupleList =[]
            for i in range(len(v)-1):
                for j in range(i+1,len(v)): tupleList.append([v[i],v[j]])
            tuplePosMap[k]=tupleList
        return tuplePosMap

    def noWhereToMove(self,toTuples):
         return len(toTuples)==0

    def forcedMove(self,toTuples):
        return len(toTuples) == 1

    def moveFormsALoopInAnIsolatedPathCase1(self,isolatedPath, fromNode, toNode, path):
        if len(path)==self.goalLength-1: return False
        return len(isolatedPath.intersection({fromNode,toNode}))==2 and not self.getOrderedPath(toNode,fromNode) in path

    def moveFormsALoopInAnIsolatedPathCase2(self,isolatedPath, fromNode, toNode1, toNode2, path):
        if len(path)==self.goalLength-2: return False
        return not fromNode in isolatedPath and  len(isolatedPath.intersection({toNode1,toNode2}))==2

    def finalStepLoop(self,path):
        return len(path)==self.goalLength-1

    def moveFormsALoop(self,fromNode, toTuple, isolatedPaths, path):
        if self.finalStepLoop(path): return False
        t1,t2 = toTuple
        for isolatedPath in isolatedPaths:
            if self.moveFormsALoopInAnIsolatedPathCase1(isolatedPath,fromNode,t1,path) or\
                    self.moveFormsALoopInAnIsolatedPathCase1(isolatedPath,fromNode,t2,path) or\
                    self.moveFormsALoopInAnIsolatedPathCase2(isolatedPath,fromNode,t1,t2,path):
                return True
        return False

    def updateIsolatedPaths(self,fromNode, tuple,isolatedPaths):
        t1,t2 = tuple
        moveSet = {fromNode,t1,t2}
        mergeList=[]
        for i in range(len(isolatedPaths)):
            isolatedPath = isolatedPaths[i]
            if len(isolatedPath.intersection(moveSet))>0:
                isolatedPath.update(moveSet)
                mergeList.append(i)
        if len(mergeList)==0:
            isolatedPaths.append(set(moveSet))
        elif len(mergeList)==2:
            isolatedPaths[mergeList[0]].update(isolatedPaths[mergeList[1]])
            del isolatedPaths[mergeList[1]]
        elif len(mergeList)>2:
            print "A move can not combine more than two isolated paths. Something wrong in updateIsolatedPaths"

    def move(self,fromNode,toTuple,isolatedPaths, tuplePosMap, path,sweepExceptions,sweptNodes):
        toBeSweptNodes=[]
        self.updateSweep(toBeSweptNodes,fromNode,toTuple,path,sweepExceptions)
        self.updateIsolatedPaths(fromNode, toTuple,isolatedPaths)
        self.updateTuplePosMap(fromNode, toTuple, tuplePosMap,sweepExceptions,toBeSweptNodes,sweptNodes)
        self.updatePath(fromNode,toTuple, path)
        self.loopPrune(tuplePosMap,path,isolatedPaths)

    def combinedIsolatedPathLength(self,isolatedPaths):
        l= set()
        for isolatedPath in isolatedPaths:
            l.update(isolatedPath)
        return len(l)

    def prune(self,path,isolatedPaths,tuplePosMap,sweepExceptions,sweptNodes):
            if self.goalSatisfied(sweptNodes,path):
                return "solution found"
            for fromNode, toTuples in tuplePosMap.iteritems():
                    if self.noWhereToMove(toTuples): return "reject"
                    elif self.forcedMove(toTuples):
                        if self.moveFormsALoop(fromNode,toTuples[0], isolatedPaths,path): return "reject"
                        self.move(fromNode,toTuples[0],isolatedPaths, tuplePosMap, path,sweepExceptions,sweptNodes)
                        return self.prune(path,isolatedPaths,tuplePosMap,sweepExceptions,sweptNodes)
            return "accept"

    def goalSatisfied(self,sweptNodes,path):
        return len(sweptNodes)==self.goalLength and len(path)==self.goalLength


    def takeAMoveOutInAll(self,move,exceptionList, tuplePosMap):
        for k,vs in tuplePosMap.iteritems():
                 if k in exceptionList: continue
                 tuplePosMap[k] = [v for v in vs if not move in v]

    def constrainBasedOnIncomingLeg(self,fromNode,tuple, tuplePosMap):
         for toNode in tuple:
            if toNode in tuplePosMap:
                t1v = tuplePosMap[toNode]
                tuplePosMap[toNode] = [v for v in t1v if fromNode in v]


    def deleteFromTuplePosMap(self,node,tuplePosMap):
        if node in tuplePosMap: del tuplePosMap[node]

    def sweepNodes(self,toBeSweptNodes,sweepExceptions, tuplePosMap):
        for node in toBeSweptNodes:
            self.takeAMoveOutInAll(node,sweepExceptions[node], tuplePosMap)
            if node in tuplePosMap: self.deleteFromTuplePosMap(node,tuplePosMap)

    def loopPrune(self,tuplePosMap,path,isolatedPaths):
        for k,v in tuplePosMap.iteritems():
            tuplePosMap[k]=[toTuple for toTuple in v if not self.moveFormsALoop(k, toTuple, isolatedPaths, path)]


    def updateTuplePosMap(self,fromNode, toTuple, tuplePosMap,sweepExceptions,toBeSweptNodes,sweptNodes):
        toBeSweptNodes = [v for v in toBeSweptNodes if v not in sweptNodes]
        self.sweepNodes(toBeSweptNodes,sweepExceptions, tuplePosMap)
        sweptNodes.extend(toBeSweptNodes)
        self.constrainBasedOnIncomingLeg(fromNode, toTuple,tuplePosMap)

    def copyParams(self,posMap, isolatedPaths, path, sweepExceptions,sweptNodes):
        return copy.deepcopy(posMap),copy.deepcopy(isolatedPaths),path[:], copy.deepcopy(sweepExceptions),  sweptNodes[:]

    def getOrderedPath(self,node1,node2):
        if node1< node2: node = [node1,node2]
        else: node = [node2,node1]
        return node

    def appendToPathInOrder(self,node1,node2, path):
        node = self.getOrderedPath(node1,node2)
        if node not in path: path.append(node)

    def updatePath(self,fromNode,toTuple, path):
        t1,t2 = toTuple
        self.appendToPathInOrder(t1,fromNode, path)
        self.appendToPathInOrder(t2,fromNode, path)

    def updateSweepOneNode(self,toBeSweptNodes,fromNode,t1,path,sweepExceptions):
        if t1 in sum(path,[]):
            toBeSweptNodes.append(t1)
            sweepExceptions[t1].append(fromNode)
        else:
            sweepExceptions[t1] = [fromNode]

    def updateSweep(self,toBeSweptNodes,fromNode,toTuple,path,sweepExceptions):
        toBeSweptNodes.append(fromNode)
        t1,t2 = toTuple
        sweepExceptions[fromNode] = toTuple
        self.updateSweepOneNode(toBeSweptNodes,fromNode,t1,path,sweepExceptions)
        self.updateSweepOneNode(toBeSweptNodes,fromNode,t2,path,sweepExceptions)

    def display(self,path):
        print time.clock() - self.startTime, "seconds process time"
        print "solution found"
        self.draw(path,"Solution found")
        print path
        quit()

    def storeCurrentValuesBeforeMakingAMove(self,tuplePosMap,isolatedPaths,path,sweepExceptions,sweptNodes):
        return self.copyParams(tuplePosMap,isolatedPaths,path,sweepExceptions,sweptNodes)

    def backtrack(self,tuplePosMapPrev,isolatedPathsPrev,pathPrev,sweepExceptionsPrev,sweptNodesPrev):
        return self.copyParams(tuplePosMapPrev,isolatedPathsPrev,pathPrev,sweepExceptionsPrev,sweptNodesPrev)

    def removeNonWorkingMoveForPruning(self,tuplePosMap,fromNode,toTuple):
        if fromNode in tuplePosMap:
            if toTuple in tuplePosMap[fromNode]:
                tuplePosMap[fromNode].remove(toTuple)

    def search(self,path,isolatedPaths, tuplePosMap, sweepExceptions,sweptNodes):
        if self.goalSatisfied(sweptNodes,path):
            return "solution found"
        else:
                keys = copy.copy(tuplePosMap.keys())
                shuffle(keys)
                for fromNode in keys:
                    toTuples=tuplePosMap[fromNode]
                    for toTuple in toTuples:
                        if self.moveFormsALoop(fromNode, toTuple, isolatedPaths,path):
                            self.removeNonWorkingMoveForPruning(tuplePosMap,fromNode,toTuple)
                            continue
                        tuplePosMapPrev,isolatedPathsPrev,pathPrev,sweepExceptionsPrev,sweptNodesPrev = \
                            self.storeCurrentValuesBeforeMakingAMove(tuplePosMap,isolatedPaths,path,sweepExceptions,sweptNodes)
                        self.move(fromNode,toTuple,isolatedPaths, tuplePosMap, path,sweepExceptions,sweptNodes)
                        statusAfterPruning = self.prune(path, isolatedPaths,tuplePosMap,sweepExceptions,sweptNodes)
                        if statusAfterPruning == "accept":
                            if self.animate: self.draw(path,"intermediate-after-pruning")
                            statusAfterSearch = self.search(path,isolatedPaths,tuplePosMap,sweepExceptions,sweptNodes)
                            if self.animate: self.draw(path,"intermediate-after-search")
                        elif statusAfterPruning == "reject":
                            tuplePosMap,isolatedPaths,path,sweepExceptions,sweptNodes = \
                                self.backtrack(tuplePosMapPrev,isolatedPathsPrev,pathPrev,sweepExceptionsPrev,sweptNodesPrev)
                            self.removeNonWorkingMoveForPruning(tuplePosMap,fromNode,toTuple)
                            continue
                        elif statusAfterPruning == "solution found":
                            statusAfterSearch=statusAfterPruning
                        if statusAfterSearch == "solution found":
                             self.display(path)
                        elif statusAfterSearch == "reject":
                            tuplePosMap,isolatedPaths,path,sweepExceptions,sweptNodes = \
                                self.backtrack(tuplePosMapPrev,isolatedPathsPrev,pathPrev,sweepExceptionsPrev,sweptNodesPrev)
                            self.removeNonWorkingMoveForPruning(tuplePosMap,fromNode,toTuple)
                            continue
                if self.animate: self.draw(path,"backtrack")
                return "reject"

    @staticmethod
    def puzzleSolve(rows=8,cols=8, animate=True):
        t0 = time.clock()
        puzzle = KnightsTour(rows,cols, t0, animate)
        path = []
        isolatedPaths=[]
        sweepExceptions={}
        sweptNodes=[]
        posMap = puzzle.getPossibilitiesMap()
        tuplePosMap = puzzle.convertPossibilitiesToTuples(posMap)
        status = puzzle.prune(path,isolatedPaths, tuplePosMap, sweepExceptions,sweptNodes)
        puzzle.draw(path,"After Initial Pruning")
        if status=="reject":
            print "No solution"
        elif status == "solution found":
            puzzle.display(path)
        else:
            status=puzzle.search(path,isolatedPaths, tuplePosMap, sweepExceptions,sweptNodes)
        if status=="reject":
            print time.clock() - t0, "seconds process time"
            puzzle.draw(path, "No solution")
            print "No solution"
        else: puzzle.display(path)



if __name__ == '__main__':
    KnightsTour.puzzleSolve(8,8, False)
